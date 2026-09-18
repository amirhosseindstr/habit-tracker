const API_BASE = "/api";

const habitList = document.getElementById("habit-list");
const addForm = document.getElementById("add-form");

async function fetchHabits() {
  const res = await fetch(`${API_BASE}/habits`);
  const habits = await res.json();
  renderHabits(habits);
}

function renderHabits(habits) {
  habitList.innerHTML = "";
  if (habits.length === 0) {
    habitList.innerHTML = `<p style="text-align:center;color:#888;">هنوز عادتی اضافه نکردی 👀</p>`;
    return;
  }

  habits.forEach((habit) => {
    const card = document.createElement("div");
    card.className = "habit-card";
    card.innerHTML = `
      <div class="habit-info">
        <span class="habit-icon">${habit.icon}</span>
        <div>
          <div class="habit-name">${habit.name}</div>
          <div class="streak-badge">🔥 ${habit.streak} روز پشت‌سرهم</div>
        </div>
      </div>
      <div>
        <button class="check-btn ${habit.done_today ? "done" : ""}" data-id="${habit.id}">
          ${habit.done_today ? "انجام شد ✅" : "انجام دادم"}
        </button>
        <button class="delete-btn" data-id="${habit.id}">🗑️</button>
      </div>
    `;
    habitList.appendChild(card);
  });

  document.querySelectorAll(".check-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!btn.classList.contains("done")) checkHabit(btn.dataset.id);
    });
  });

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => deleteHabit(btn.dataset.id));
  });
}

async function checkHabit(id) {
  await fetch(`${API_BASE}/habits/${id}/check`, { method: "POST" });
  fetchHabits();
}

async function deleteHabit(id) {
  await fetch(`${API_BASE}/habits/${id}`, { method: "DELETE" });
  fetchHabits();
}

addForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("habit-name").value.trim();
  const icon = document.getElementById("habit-icon").value;
  if (!name) return;

  await fetch(`${API_BASE}/habits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, icon }),
  });

  document.getElementById("habit-name").value = "";
  fetchHabits();
});

fetchHabits();
