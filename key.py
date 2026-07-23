import discord
from discord.ext import commands
import datetime

# Banco de dados simulado em memória (compartilhado entre os arquivos)
DATABASE_KEYS = {}
SERVIDORES_ATIVADOS = {}

# Modals e Views do Sistema de Keys
class ModalGerarKey(discord.ui.Modal, title="Gerar Nova Key"):
    dias = discord.ui.TextInput(label="Quantos dias de key?", placeholder="Ex: 30", required=True, max_length=4)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd_dias = int(self.dias.value)
        except ValueError:
            await interaction.response.send_message("❌ Digite apenas números válidos!", ephemeral=True)
            return

        import uuid
        nova_key = str(uuid.uuid4()).upper()
        expira = datetime.datetime.now() + datetime.timedelta(days=qtd_dias)

        DATABASE_KEYS[nova_key] = {
            "dias": qtd_dias,
            "gerado_por": interaction.user.name,
            "expira_em": expira,
            "ativo": True
        }

        embed = discord.Embed(
            title="✅ Key Gerada com Sucesso!",
            description=f"Aqui está a sua nova key:\n```{nova_key}```\n**Validade:** {qtd_dias} dias",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ModalCancelarKey(discord.ui.Modal, title="Cancelar Key"):
    chave = discord.ui.TextInput(label="Digite a key que quer cancelar", placeholder="Cole a key aqui...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        key_digitada = self.chave.value.strip()
        if key_digitada in DATABASE_KEYS:
            del DATABASE_KEYS[key_digitada]
            await interaction.response.send_message(f"🗑️ A key `{key_digitada}` foi cancelada!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Key não encontrada!", ephemeral=True)

class PainelKeyView(discord.ui.View):
    def __init__(self, meu_id):
        super().__init__(timeout=None)
        self.meu_id = meu_id

    @discord.ui.button(label="Gerar Key", style=discord.ButtonStyle.green, custom_id="btn_gerar_key")
    async def gerar_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.meu_id:
            await interaction.response.send_message("❌ Apenas o dono!", ephemeral=True)
            return
        await interaction.response.send_modal(ModalGerarKey())

    @discord.ui.button(label="Ver Keys", style=discord.ButtonStyle.blurple, custom_id="btn_ver_key")
    async def ver_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.meu_id:
            await interaction.response.send_message("❌ Apenas o dono!", ephemeral=True)
            return
        if not DATABASE_KEYS:
            await interaction.response.send_message("📂 Nenhuma key gerada.", ephemeral=True)
            return

        embed = discord.Embed(title="🔑 Keys Ativas", color=discord.Color.blue())
        for chave, dados in DATABASE_KEYS.items():
            tempo_restante = dados["expira_em"] - datetime.datetime.now()
            dias_restantes = max(0, tempo_restante.days)
            embed.add_field(name=f"Key: {chave[:8]}...", value=f"**Gerado por:** {dados['gerado_por']}\n**Dias:** {dias_restantes}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Cancelar Key", style=discord.ButtonStyle.red, custom_id="btn_cancelar_key")
    async def cancelar_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.meu_id:
            await interaction.response.send_message("❌ Apenas o dono!", ephemeral=True)
            return
        await interaction.response.send_modal(ModalCancelarKey())

# Função para registrar os comandos de keys no bot principal
def setup_keys(bot, meu_id):
    @bot.command(name="criar-key")
    async def criar_key(ctx):
        if ctx.author.id != meu_id and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Apenas o dono pode usar este comando!")
            return
        
        embed = discord.Embed(title="Painel de Keys", description="Use os botões abaixo:", color=discord.Color.gold())
        await ctx.send(embed=embed, view=PainelKeyView(meu_id))

    @bot.command(name="ativar")
    async def ativar(ctx, chave: str = None):
        if not chave:
            await ctx.send("❌ Use: `!ativar SUA-CHAVE-AQUI`")
            return

        if chave in DATABASE_KEYS and DATABASE_KEYS[chave]["ativo"]:
            SERVIDORES_ATIVADOS[ctx.guild.id] = True
            await ctx.send("✅ Key ativada com sucesso! O comando `!painel` foi liberado.")
        else:
            await ctx.send("❌ Key inválida ou inexistente!")
