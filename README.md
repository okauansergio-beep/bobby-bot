# Bobby Bot: fluxo 100% gratuito e automático

Você configura UMA vez. Depois o robô repõe a fila de posts, cria as artes e posta 2x por dia sozinho.

## O que você faz 1 vez
1. **Poses do Bobby:** gere 10 a 20 imagens do Bobby (fundo preto, sem texto) nas IAs de imagem e coloque na pasta `bobby_poses/`. Varie pose, cenário e roupa (astronauta, terno, etc.).
2. **Briefing:** edite `briefing.md` com o tom e os temas (já vem preenchido).
3. **Fonte (opcional):** ponha uma fonte .ttf da sua escolha em `fonts/fonte.ttf` (ex.: Google Fonts). Se não, usa uma padrão.
4. **GitHub:** crie um repositório **público** (o Instagram precisa de link público da imagem) e suba todo esse conteúdo.
5. **Chave do Gemini (grátis):** em aistudio.google.com/apikey crie uma chave.
6. **Instagram API (grátis):**
   - Conta Instagram **Profissional** (Criador/Empresa) ligada a uma **Página do Facebook**.
   - Em developers.facebook.com crie um app (tipo Business), adicione o produto "Instagram Graph API" e permissões `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
   - No Graph API Explorer gere um token, troque por token de longa duração e depois pegue o **token da Página** (esse não expira). Pegue também o **IG_USER_ID** (`/me/accounts` -> página -> `?fields=instagram_business_account`).
7. **Segredos:** no repositório, Settings > Secrets and variables > Actions, crie: `GEMINI_API_KEY`, `IG_USER_ID`, `IG_TOKEN`.
8. Aba **Actions** > "Bobby Bot" > **Run workflow** para testar. Pronto.

## Como funciona
- `manter`: se tiver menos de 7 posts prontos, o Gemini cria 14 ideias novas (texto + legenda) e o Pillow monta as artes (texto por cima da pose do Bobby, sem erro de português).
- `postar`: publica o próximo da fila no Instagram.
- Roda sozinho às 12h e 20h (horário de Brasília). Mude o `cron` em `.github/workflows/bobby.yml`.

## Controle de qualidade
- Quer aprovar antes? Abra `fila.json` no GitHub e apague ou edite os posts com status `"pronto"`.
- Para pausar: Actions > Bobby Bot > `...` > Disable workflow.

## Limites e avisos
- O Instagram permite até ~25 posts por dia pela API; 2 por dia está longe disso.
- Os planos gratuitos (Gemini, GitHub Actions, Graph API) podem mudar de limite; se `GEMINI_MODEL` mudar de nome, defina o novo em `GEMINI_MODEL`.
- Se a Meta bloquear o token, gere outro (passo 6).
