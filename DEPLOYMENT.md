# Deployment

This project can deploy as one public web service. The Docker image builds the Vue frontend, copies it into the FastAPI app, and serves both the API and the final UI from the same domain.

## Render

1. Push this repository to GitHub.
2. Open Render and create a new Blueprint from the repository.
3. Render will detect `render.yaml` and create one Docker web service.
4. After deploy, open the generated `https://...onrender.com` URL.

The API docs will be available at `/docs`, and the app routes such as `/predictions` are served by the same service.

## Manual Docker

```powershell
docker build -t supply-chain-command-centre .
docker run --rm -p 8000:8000 supply-chain-command-centre
```

Then open `http://127.0.0.1:8000`.
