const tokenInput = document.querySelector("#token");
const saveButton = document.querySelector("#save");
const launchButton = document.querySelector("#launch");
const statusLine = document.querySelector("#status");
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
    body: JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok || result.ok !== true) throw new Error(result.error || "操作失败，请检查后重试。");
  return result;
}

saveButton.addEventListener("click", async () => {
  if (!tokenInput.value.trim()) {
    statusLine.className = "status error";
    statusLine.textContent = "请先粘贴 ProcessOn Token。";
    tokenInput.focus();
    return;
  }
  statusLine.className = "status";
  statusLine.textContent = "正在安全保存…";
  saveButton.disabled = true;
  try {
    await post("/api/credentials", { token: tokenInput.value });
    statusLine.className = "status success";
    statusLine.textContent = "保存成功。现在可以打开 Codex。";
    launchButton.disabled = false;
  } catch (error) {
    statusLine.className = "status error";
    statusLine.textContent = error instanceof Error ? error.message : "Token 保存失败。";
  } finally {
    tokenInput.value = "";
    saveButton.disabled = false;
    tokenInput.focus();
  }
});

launchButton.addEventListener("click", async () => {
  launchButton.disabled = true;
  try {
    await post("/api/launch", {});
    statusLine.className = "status success";
    statusLine.textContent = "Codex 已打开。请新建任务并继续 ProcessOn 制图。";
  } catch {
    statusLine.className = "status error";
    statusLine.textContent = "无法自动打开 Codex，请手动重新打开应用。";
    launchButton.disabled = false;
  }
});
