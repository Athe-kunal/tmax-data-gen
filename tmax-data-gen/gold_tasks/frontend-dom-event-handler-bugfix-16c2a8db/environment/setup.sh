mkdir -p /home/user/app
cat > /home/user/app/index.html << 'HTML_EOF'
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Counter</title></head>
<body>
  <h1>Click Counter</h1>
  <p>Count: <span id="count">0</span></p>
  <button id="increment">+1</button>
  <script src="script.js"></script>
</body>
</html>

HTML_EOF
cat > /home/user/app/script.js << 'JS_EOF'
let count = 0;

document.getElementById("increment").addEventListener("click", function () {
  const display = document.getElementById("count");
  const shown = display.textContent;
  count += 2;
  display.textContent = shown;
  display.textContent = String(count - 1);
});

JS_EOF

