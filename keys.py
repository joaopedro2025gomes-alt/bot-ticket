import discord
from discord.ext import commands
from keys import setup_keys, SERVIDORES_ATIVADOS # Importa o arquivo de keys

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CONFIGURAÇÕES =================
MEU_ID = 1474550396813971550 # Coloque o seu ID aqui
# =================================================

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')

# Carrega os comandos do arquivo keys.py
setup_keys(bot, MEU_ID)

# --- COMANDO !PAINEL (DO SEU BOT DE TICKETS) ---
@bot.command(name="painel")
async def painel(ctx):
    # Verifica se o servidor já ativou a key importada do outro arquivo
    if ctx.guild.id not in SERVIDORES_ATIVADOS:
        await ctx.send("⚠️ Coloque sua key em `!ativar <sua_key>` antes de usar este comando!")
        return

    embed = discord.Embed(
        title="Painel de Tickets",
        description="Bem-vindo ao painel oficial!",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
