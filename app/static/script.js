const API_URL = "http://127.0.0.1:8000/books";

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
                : ""
            }
            <strong>${book.title}</strong> - ${book.author} (${
      book.year || "Ano N/D"
    })
            <button onclick="deleteBook(${book.id})">Excluir</button>
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
