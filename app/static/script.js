const API_URL = "/books";

async function fetchBooks() {
  const res = await fetch(API_URL);
  const books = await res.json();
  const container = document.getElementById("book-list");
  container.innerHTML = "";
  books.forEach((book) => {
    const div = document.createElement("div");
    div.className = "book-card";
    div.innerHTML = `
            ${
              book.image_url
                ? `<img src="${book.image_url}" alt="${book.title}">`
                : '<div style="height:180px; background:#f0f0f0; display:flex; align-items:center; justify-content:center; color:#ccc;">📖</div>'
            }
            <div class="book-card-content">
              <h3>${book.title}</h3>
              <p><strong>Autora:</strong> ${book.author}</p>
              <p><strong>Ano:</strong> ${book.year || "N/D"}</p>
              <div class="card-actions">
                <button class="edit-btn" onclick="openEditModal(${JSON.stringify(
                  book
                ).replace(/"/g, "&quot;")})">Editar ✏️</button>
                <button class="delete-btn" onclick="deleteBook(${
                  book.id
                })">Excluir 🗑️</button>
              </div>
            </div>
        `;
    container.appendChild(div);
  });
}

// Lógica de Edição
function openEditModal(book) {
  document.getElementById("edit-id").value = book.id;
  document.getElementById("edit-title").value = book.title;
  document.getElementById("edit-author").value = book.author;
  document.getElementById("edit-year").value = book.year || "";
  document.getElementById("edit-image_url").value = book.image_url || "";
  document.getElementById("edit-modal").style.display = "block";
}

function closeEditModal() {
  document.getElementById("edit-modal").style.display = "none";
}

window.onclick = function (event) {
  const modal = document.getElementById("edit-modal");
  if (event.target == modal) closeEditModal();
};

document
  .getElementById("edit-book-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("edit-id").value;
    const data = {
      title: document.getElementById("edit-title").value,
      author: document.getElementById("edit-author").value,
      year: parseInt(document.getElementById("edit-year").value) || null,
      image_url: document.getElementById("edit-image_url").value || null,
    };

    await fetch(`${API_URL}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    closeEditModal();
    fetchBooks();
  });

document.getElementById("book-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = {
    title: document.getElementById("title").value,
    author: document.getElementById("author").value,
    year: parseInt(document.getElementById("year").value) || null,
    image_url: document.getElementById("image_url").value || null,
  };
  await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  document.getElementById("book-form").reset();
  fetchBooks();
});

async function deleteBook(id) {
  if (confirm("Tem certeza que deseja excluir este tesouro? 🥺")) {
    await fetch(`${API_URL}/${id}`, { method: "DELETE" });
    fetchBooks();
  }
}

fetchBooks();
