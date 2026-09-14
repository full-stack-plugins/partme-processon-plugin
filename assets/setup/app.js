const tokenInput = document.querySelector("#token");
const saveButton = document.querySelector("#save");
const statusLine = document.querySelector("#status");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

saveButton.addEventListener("click", async () => {
  if (!tokenInput.value.trim()) {
    statusLine.className = "status error";
    statusLine.textContent = "请先粘贴 ProcessOn Token。";
    tokenInput.focus();
    return;
  }
  saveButton.disabled = true;
  statusLine.className = "status pending";
  statusLine.textContent = "正在安全保存…";
  try {
    const response = await fetch("/api/credentials", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({ token: tokenInput.value }),
    });
    const result = await response.json();
    if (!response.ok || result.ok !== true) throw new Error();
    statusLine.className = "status success";
    statusLine.textContent = "保存成功，请重新打开 Codex 开始使用。";
  } catch {
    statusLine.className = "status error";
    statusLine.textContent = "保存失败，请检查 Token 后重试。";
  } finally {
    tokenInput.value = "";
    saveButton.disabled = false;
    tokenInput.focus();
  }
});
