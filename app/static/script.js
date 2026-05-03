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
              <button class="delete-btn" onclick="deleteBook(${book.id})">Excluir 🗑️</button>
            </div>
        `;
    container.appendChild(div);
  });
}

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
  await fetch(`${API_URL}/${id}`, { method: "DELETE" });
  fetchBooks();
}

fetchBooks();
