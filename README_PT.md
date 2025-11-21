# AIVidFromPPT

Um serviço de geração de vídeo com IA baseado em FastAPI que suporta um fluxo de trabalho completo de PPT para vídeo, incluindo análise de PPT, conversão de texto em fala, síntese de vídeo e funcionalidade de humano virtual.

Este projeto fornece serviços de interface de API para a plataforma Maker. Após a implantação, é necessário configurar o endereço de rede pública no nó HOST ENDPOINT do Maker para chamar as interfaces de API deste serviço nos fluxos de trabalho do Maker.

## ✨ Funcionalidades

- 📄 **Análise e Processamento de PPT** - Converter arquivos PPT/PPTX em imagens com gerenciamento de contexto
- 🔊 **Conversão de Texto em Fala (TTS)** - Suporte para múltiplos provedores de TTS com geração automática de legendas
- 📤 **Gerenciamento de Upload de Arquivos** - Fazer upload, baixar e gerenciar vários tipos de arquivos
- 🎬 **Síntese de Vídeo** - Combinar imagens, áudio, legendas e vídeos de humano virtual em vídeos completos
- 👤 **Síntese de Humano Virtual** - Gerar vídeos de humano virtual com sincronização labial baseada em texto

## 🚀 Início Rápido

### Requisitos

- Python 3.11+
- Docker (opcional, para implantação containerizada)

### Configuração do Código Fonte

1. **Clonar o repositório**

```bash
git clone <repository-url>
cd hackathon-AIVidFromPPT
```

2. **Instalar dependências do sistema**

O projeto requer as seguintes ferramentas do sistema. Instale-as de acordo com seu sistema operacional:

#### macOS

```bash
# Instalar usando Homebrew
brew install libreoffice poppler ffmpeg fontconfig
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    poppler-utils \
    ffmpeg \
    fontconfig
```

#### Windows

- **LibreOffice**: Baixar e instalar do [site oficial](https://www.libreoffice.org/download/)
- **Poppler**: Baixar do [GitHub](https://github.com/oschwartz10612/poppler-windows/releases), extrair e adicionar ao PATH
- **FFmpeg**: Baixar do [site oficial](https://ffmpeg.org/download.html), extrair e adicionar ao PATH
- **Fontconfig**: Geralmente incluído no sistema

**Notas**:
- `libreoffice` - Para converter arquivos PPT/PPTX em imagens
- `poppler-utils` - Para processamento de PDF e extração de imagens
- `ffmpeg` - Para processamento de vídeo e áudio
- `fontconfig` - Para gerenciamento de fontes (suporte a fontes chinesas)

3. **Criar ambiente virtual**

```bash
conda create -n aividfromppt python=3.11 -y
conda activate aividfromppt
```

4. **Instalar dependências Python**

```bash
cd server
pip install -r requirements.txt
```

5. **Configurar variáveis de ambiente**

Criar um arquivo `.env` (ou copiar de `.env.example`):

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

6. **Iniciar o serviço**

```bash
uvicorn main:app --host 0.0.0.0 --port 8201 --reload
```

7. **Acessar documentação da API**

Abra seu navegador e visite: http://localhost:8201/docs

## 🐳 Implantação Docker

### Recomendações de Configuração do Servidor

Para garantir a operação estável do serviço, recomenda-se usar um servidor em nuvem com a seguinte configuração:

- **Configuração Recomendada**: 8 núcleos de CPU + 16GB de RAM
- **Configuração Mínima**: 4 núcleos de CPU + 8GB de RAM
- **Armazenamento**: Pelo menos 50GB de espaço disponível (para armazenar arquivos enviados e vídeos gerados)

**Notas**:
- A síntese de vídeo e a geração de humano virtual são tarefas intensivas em computação que requerem recursos suficientes de CPU e memória
- Mais memória ajuda a processar arquivos PPT e vídeo grandes
- Espaço de armazenamento suficiente é necessário para salvar arquivos enviados pelos usuários e vídeos gerados

### Usando variáveis de ambiente

```bash
docker run -d \
  --name aividfromppt \
  --restart=always \
  -p 8201:8201 \
  -e OPENAI_API_KEY="your-openai-api-key-here" \
  -v $(pwd)/server/uploads:/app/uploads \
  unhejing/aividfromppt:latest
```

### 🌐 Serviço Online (Sem Implantação Local Necessária)

Se você não tiver um ambiente de implantação local, pode usar diretamente nosso serviço online para testes:

- **Endereço do Serviço**: `http://154.40.41.212:8201`
- **Documentação da API**: `http://154.40.41.212:8201/docs`
- **Documentação Interativa**: `http://154.40.41.212:8201/redoc`

**Notas de Uso**:
- Todos os endpoints da API podem ser acessados diretamente através do endereço acima
- Ao configurar HOST ENDPOINT na plataforma Maker, use `http://154.40.41.212:8201` como endereço do serviço
- Não é necessário instalar dependências ou configurar o ambiente, pronto para uso imediato

## 📚 Documentação da API

Todos os endpoints da API seguem convenções RESTful com caminho base `/api/v1`.

### Análise e Processamento de PPT (`/api/v1/pptToImg`)

- `POST /upload` - Fazer upload de arquivo PPT/PPTX e converter em imagens
- `GET /image` - Obter imagens convertidas
- `POST /context` - Adicionar dados de contexto
- `PUT /context` - Atualizar dados de contexto
- `DELETE /context` - Excluir dados de contexto
- `GET /context/{uuid}` - Obter dados de contexto

### Conversão de Texto em Fala (`/api/v1/tts`)

- `POST /synthesize` - Síntese de texto em fala
  - Suporta OpenAI TTS
  - Gera automaticamente arquivos de legenda SRT
  - Retorna URL do arquivo de áudio e metadados
- `GET /files/{file_path}` - Obter arquivos de áudio ou legenda
- `GET /channels` - Obter lista de canais TTS suportados

### Upload de Arquivos (`/api/v1/upload`)

- `POST /file` - Fazer upload de um único arquivo (máx. 50MB)
- `POST /files` - Fazer upload de múltiplos arquivos
- `GET /files/{file_path}` - Obter arquivo enviado
- `DELETE /file/{file_path}` - Excluir arquivo
- `GET /list` - Listar todos os arquivos enviados

Tipos de arquivo suportados: imagens, documentos, vídeos, áudio, legendas, arquivos compactados, etc.

### Síntese de Vídeo (`/api/v1/video`)

- `POST /synthesize` - Sintetizar vídeo
  - Suporta síntese de vídeo multi-segmento
  - Suporta sobreposição de imagens, áudio, legendas e vídeos de humano virtual
  - Retorna ID do vídeo e URL de acesso
- `GET /{video_id}` - Obter informações do vídeo
- `GET /{video_id}/download` - Baixar arquivo de vídeo
- `GET /health` - Verificação de saúde

### Humano Virtual (`/api/v1/virtual`)

- `POST /generate-video` - Gerar vídeo de humano virtual
  - Gerar vídeo com sincronização labial baseado em texto
  - Suporta conteúdo misto em chinês e inglês
  - Suporta seleção de gênero

## 🛠️ Stack Tecnológico

- **Framework Web**: FastAPI
- **Versão Python**: 3.11
- **Principais Dependências**:
  - OpenAI API (TTS)
  - MoviePy (Processamento de vídeo)
  - PyMuPDF (Processamento de PDF)
  - LibreOffice (Conversão de PPT)
  - FFmpeg (Processamento de vídeo/áudio)

## 📁 Estrutura do Projeto

```
hackathon-AIVidFromPPT/
├── server/                 # Serviço backend
│   ├── pptToImg/          # Análise e processamento de PPT
│   ├── tts/               # Conversão de texto em fala
│   ├── upload/            # Gerenciamento de upload de arquivos
│   ├── video/             # Síntese de vídeo
│   ├── virtual/           # Síntese de humano virtual
│   ├── main.py            # Ponto de entrada da aplicação
│   └── requirements.txt   # Dependências Python
├── .setup/                # Configuração de implantação
│   ├── Dockerfile         # Build da imagem Docker
│   └── build_and_push_dockerhub.sh  # Script de build da imagem
├── docs/                  # Documentação do projeto
└── README.md              # Descrição do projeto
```

## 📝 Variáveis de Ambiente

| Variável | Obrigatório | Descrição | Padrão |
|----------|-------------|-----------|--------|
| `OPENAI_API_KEY` | ✅ | Chave da API OpenAI | Nenhum |

## 🔧 Configuração do Maker

### Configuração do HOST ENDPOINT

Após a implantação, é necessário configurar o nó HOST ENDPOINT na plataforma Maker:

1. Obter o endereço de rede pública do seu serviço (por exemplo: `http://your-domain.com` ou `http://your-ip:8201`)
2. Adicionar um nó HOST ENDPOINT no seu fluxo de trabalho do Maker
3. Inserir o endereço de rede pública na configuração do nó

Exemplo de configuração:

![Configuração do Host Endpoint](./resource/hostConfig.png)

**Notas de Configuração**:
- Inserir o endereço de rede pública no campo Template, por exemplo: `http://154.40.41.212:8201`
- Garantir que o serviço está corretamente implantado e acessível da rede pública
- Após a configuração, você pode chamar todas as interfaces de API deste serviço nos fluxos de trabalho do Maker

## 🎬 Vídeos de Demonstração

A seguir estão exemplos de resultados de vídeo gerados chamando este serviço através da plataforma Maker:

> **Nota**: O README do GitHub não suporta reprodução direta de vídeo. Por favor, clique nos links abaixo para baixar e visualizar os vídeos, ou use um visualizador de Markdown que suporte reprodução de vídeo.

### Arquivo Original

📄 [Baixar Arquivo PPT Original](./resource/test.pptx) - Este é o arquivo fonte usado para gerar os vídeos

### Demonstração em Chinês

📹 [Baixar Vídeo de Demonstração em Chinês](./resource/cn_video_res.mp4)

### Demonstração em Inglês

📹 [Baixar Vídeo de Demonstração em Inglês](./resource/en_video_res.mp4)

### Demonstração em Português

📹 [Baixar Vídeo de Demonstração em Português](./resource/pt_video_res.mp4)

## 🔗 Links Relacionados

- Documentação da API: http://localhost:8201/docs
- Documentação Interativa da API: http://localhost:8201/redoc

