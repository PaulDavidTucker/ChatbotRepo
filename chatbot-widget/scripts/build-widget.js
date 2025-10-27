const fs = require("fs");
const path = require("path");

// Read the built files
const buildPath = path.join(__dirname, "../build/static");
const jsFiles = fs
  .readdirSync(path.join(buildPath, "js"))
  .filter((f) => f.endsWith(".js"));
const cssFiles = fs
  .readdirSync(path.join(buildPath, "css"))
  .filter((f) => f.endsWith(".css"));

let widgetContent = `
(function() {
  // Insert CSS
  const css = \`${fs.readFileSync(path.join(buildPath, "css", cssFiles[0]), "utf8")}\`;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  // Widget initialization
  window.initChatbot = function(config) {
    const container = document.createElement('div');
    container.id = 'chatbot-widget-root';
    document.body.appendChild(container);

    // React component would be rendered here
    // This is simplified - you'd actually bundle React and render the component
    ${fs.readFileSync(path.join(buildPath, "js", jsFiles[0]), "utf8")}
  };
})();
`;

fs.writeFileSync(
  path.join(__dirname, "../dist/chatbot-widget.js"),
  widgetContent,
);
console.log("Widget built successfully!");
