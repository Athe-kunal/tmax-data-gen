# Artifact catalog convention

The catalog mirrors Tmax's domain-first taxonomy. YAML is the source of truth;
the future sampler reads these files rather than embedding the taxonomy in code.

```text
artifacts/
  domains/<domain-id>.yaml
  skills/<domain-id>.yaml
  personas/<domain-id>.yaml
  languages/<runtime-id>.yaml
  index.yaml
  schemas/
```

- `domains/` has one file for each of the nine Tmax domains.
- `skills/` has one file per domain. It groups the domain's primitive skills by
  skill type, matching Tmax's `SKILL_TAXONOMY` structure.
- `personas/` has one file per domain. It lists that domain's task-framing
  personas, matching Tmax's `DOMAIN_SCENARIOS` structure.
- `languages/` has one file per reusable programming-language/runtime profile.
- `index.yaml` is the runtime entry point. It maps every domain to its domain,
  skill, and persona files, and maps every language ID to its profile file.

Primitive skills retain Tmax's original `description`. They may also include an
optional `guidance` object with an `origin: authored` marker, a goal, expected
operations, and optional constraints or likely tools. This enrichment improves
generation prompts without misrepresenting it as upstream Tmax data.

Every catalog file includes `schema_version: 1` and its owning stable ID.
Descriptions live on each domain, primitive skill, persona, or language record.
Relationships are expressed by IDs, not filesystem paths. A catalog index is
deferred until catalog entries exist and can be validated.
