"""Sources the cold-start (turn 0) question from tmax's own published RL
data corpus instead of generating a brand-new one - avoiding an LLM call
(and its occasional malformed-XML failures, see question_gen.py) for the
one turn that has no prior trajectory to retrieve against.

Dataset: osieosie/tmax-tasks-skill-taxonomy-20260506-legacy10k-new5k-rl
(public, ~14.6k tasks from the legacy tmax/rl_data pipeline - see
tmax/rl_data/scripts/upload/upload_data_to_hf.sh). Only the metadata
parquet is fetched: `description`/`truth`/`test_final_state`/`container_def`
are all present there. The corpus's 14.6k-task `tasks.zip` (per-task
fixture files referenced by a `%files` section) is never downloaded, so
rows whose `container_def` has one are skipped - `apply_seed_environment`
can only run a self-contained `%post`.

A row only gives `domain`/`skill_type` as strings, with no persona or
language at all, so `build_seed_sample` best-effort matches those two
against the catalog's ids/names and falls back to a random pick within the
matched domain (or a fully random domain) when nothing matches; persona and
language are always randomly sampled, same as `question_sampler.sample_entry`.
"""

from __future__ import annotations

import random
import re

import pandas as pd
from huggingface_hub import hf_hub_download

from data_gen.catalog import Catalog, DomainBundle
from data_gen.env_exec import run
from data_gen.question_gen import GeneratedQuestion
from data_gen.question_sampler import SampledEntry

_DEFAULT_REPO_ID = "osieosie/tmax-tasks-skill-taxonomy-20260506-legacy10k-new5k-rl"
_PARQUET_PATH = "data/train-00000-of-00001.parquet"
_MODEL_LABEL = "tmax-rl-data"


def load_tmax_rl_dataset(repo_id: str = _DEFAULT_REPO_ID) -> pd.DataFrame:
    """Downloads (and locally caches, via huggingface_hub) the corpus metadata parquet."""
    path = hf_hub_download(repo_id=repo_id, filename=_PARQUET_PATH, repo_type="dataset")
    return pd.read_parquet(path)


def _has_files_section(container_def: str) -> bool:
    return bool(re.search(r"^%files\b", container_def, re.MULTILINE))


def extract_base_image(container_def: str) -> str:
    """Extracts the `From:` image a row's own container_def specifies.

    Used instead of `harbor.resolve_base_image` for the seed turn: the
    row's %post (run by `apply_seed_environment`) was authored against this
    exact base, not against our best-effort-matched sample's language.
    """
    match = re.search(r"^From:\s*(\S+)", container_def, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ValueError("container_def has no From: line")
    return match.group(1)


def _extract_post_body(container_def: str) -> str:
    """Extracts the Apptainer `%post` section body (up to the next `%section` or EOF)."""
    match = re.search(r"^%post\b[^\n]*\n(.*?)(?=^%\w+|\Z)", container_def, re.DOTALL | re.MULTILINE)
    if not match:
        raise ValueError("container_def has no %post section")
    return match.group(1)


def pick_seed_row(df: pd.DataFrame, rng: random.Random | None = None) -> pd.Series:
    """Picks one row whose container_def is self-contained (no %files fixtures)."""
    rng = rng or random.Random()
    eligible = df[~df["container_def"].apply(_has_files_section)]
    if eligible.empty:
        raise ValueError("No tmax RL rows without a %files section were found")
    return eligible.iloc[rng.randrange(len(eligible))]


def _match_bundle(row: pd.Series, catalog: Catalog, rng: random.Random) -> DomainBundle:
    row_domain = str(row["domain"]).strip().lower()
    for bundle in catalog.domains:
        if bundle.domain.id == row_domain or bundle.domain.name.strip().lower() == row_domain:
            return bundle
    return rng.choice(catalog.domains)


def _match_skill_type(row: pd.Series, bundle: DomainBundle, rng: random.Random):
    row_skill_type = str(row["skill_type"]).strip().lower()
    for skill_type in bundle.skills.skill_types:
        if skill_type.id == row_skill_type or skill_type.name.strip().lower() == row_skill_type:
            return skill_type
    return rng.choice(bundle.skills.skill_types)


def build_seed_sample(row: pd.Series, catalog: Catalog, rng: random.Random | None = None) -> SampledEntry:
    """Best-effort maps a tmax RL row's domain/skill_type strings onto the
    catalog's structured objects; persona/language aren't in the row at all,
    so those are always randomly sampled, same as `sample_entry`."""
    rng = rng or random.Random()
    bundle = _match_bundle(row, catalog, rng)
    skill_type = _match_skill_type(row, bundle, rng)
    primitive = rng.choice(skill_type.primitives)
    persona = rng.choice(bundle.personas.personas)
    language = rng.choices(
        catalog.languages, weights=[language.sampling_weight for language in catalog.languages]
    )[0]
    return SampledEntry(
        domain=bundle.domain, skill_type=skill_type, primitive=primitive, persona=persona, language=language
    )


def build_seed_question(row: pd.Series, sample: SampledEntry) -> GeneratedQuestion:
    """Builds a GeneratedQuestion straight from a tmax RL row and its matched sample - no LLM call."""
    return GeneratedQuestion(
        sample=sample,
        task_description=row["description"],
        truth=row["truth"],
        test_code=row["test_final_state"],
        model=_MODEL_LABEL,
    )


def apply_seed_environment(env, row: pd.Series) -> None:
    """Runs the row's container_def `%post` body in `env` to prep the
    sandbox before the agent starts - the tmax RL corpus's own initial-state
    setup (creating git repos, oracle binaries, fixture files, etc.)."""
    run(env, _extract_post_body(row["container_def"]))
