# 📑 Roteiro de Apresentação: TheOrganizer

Este documento serve como guia para a gravação do vídeo do Trabalho 1.

---

## 🚀 Checklist de Requisitos (REQ)
- [x] **REQ01**: Empresa fictícia "TheOrganizer".
- [x] **REQ02**: Logotipo visível em todas as páginas e favicon.
- [x] **REQ03**: Domínio `theorganizer.com.br`.
- [x] **REQ04**: Aplicação exclusivamente CRUD (Livros).
- [x] **REQ05**: Tabela com 5 campos (`id`, `title`, `author`, `year`, `image_url`).
- [x] **REQ07**: Frontend em HTML/CSS puro (sem frameworks pesados).
- [x] **REQ08**: Banco de Dados MariaDB acessível via rede interna.
- [x] **REQ10/11**: DNS configurado e Autoridade Certificadora local.
- [x] **REQ14/15**: VMs separadas para Web e Banco de Dados (simuladas via containers).

---

## 🎙️ Script do Vídeo (7 a 12 minutos)

### 1. Abertura (Câmera no rosto) - [1 min]
*   Apresente-se: "Olá, professor Hermano. Eu sou a Milena Hamerski..."
*   Apresente a empresa: "**TheOrganizer** é uma plataforma premium para organização de bibliotecas pessoais."
*   Mencione o objetivo: "Demonstrar o deploy de uma aplicação CRUD em uma infraestrutura de nuvem privada automatizada."

### 2. Demonstração do CRUD (Navegador) - [3 mins]
*   Mostre o **Logotipo** e o **Favicon**.
*   **Create**: Adicione um novo livro (ex: Título: "O Alquimista", Autora: "Paulo Coelho").
*   **Read**: Mostre os cards listados com animação.
*   **Update**: Clique no ícone de lápis ✏️, altere um dado e salve.
*   **Delete**: Remova um item e mostre o alerta de confirmação 🥺.

### 3. Topologia e Infraestrutura (Terminal) - [3 mins]
*   Mostre o `docker-compose.yml` (Aumente a fonte!).
*   Explique a separação: "Temos o serviço `db` (MariaDB) e o serviço `app` (FastAPI)."
*   **Destaque Técnico**: Mostre o arquivo `infra/init.sql` e explique que o banco é inicializado automaticamente no primeiro boot.
*   Mencione o DNS e SSL: "A rede interna resolve o FQDN e os certificados garantem o tráfego seguro."

### 4. O Diferencial (O que vale +3 pontos) - [2 mins]
*   Fale sobre a **Resiliência**: "Utilizei **Healthchecks** para que a aplicação só aceite tráfego quando o banco estiver 100% pronto."
*   Fale sobre **UX/UI**: "O design utiliza Glassmorphism e é totalmente responsivo, indo além de um CRUD básico de formulários simples."

### 5. Encerramento - [1 min]
*   Resuma os ganhos: "Aprendi a orquestrar serviços, automatizar esquemas de banco de dados e gerenciar identidades em nuvem."
*   Finalize educadamente.

---

## 🛠️ Comandos de Suporte
- **Limpar tudo**: `docker-compose down -v`
- **Subir e Buildar**: `docker-compose up --build`
- **Logs em tempo real**: `docker-compose logs -f`

---

## 💡 Dica Final
Aumente as fontes do VS Code e do Terminal para que o professor consiga ler as configurações nos logs. **Boa sorte!** 🍀
