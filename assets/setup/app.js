const tokenInput = document.querySelector("#token");
const saveButton = document.querySelector("#save");
const statusLine = document.querySelector("#status");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

saveButton.addEventListener("click", async () => {
  statusLine.className = "status";
  statusLine.textContent = "正在安全保存…";
  saveButton.disabled = true;
  try {
    const response = await fetch("/api/credentials", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ token: tokenInput.value }),
    });
    const result = await response.json();
    if (!response.ok || result.ok !== true) {
      throw new Error(result.error || "Token 保存失败");
    }
    statusLine.className = "status success";
    statusLine.textContent = "保存成功。现在重新打开 Codex 即可开始使用。";
  } catch (error) {
    statusLine.className = "status error";
    statusLine.textContent = error instanceof Error ? error.message : "Token 保存失败";
  } finally {
    tokenInput.value = "";
    saveButton.disabled = false;
    tokenInput.focus();
  }
});
