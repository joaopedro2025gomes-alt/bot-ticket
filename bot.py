import discord
from discord.ext import commands
import datetime
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CONFIGURAÇÕES =================
MEU_ID = 1474550396813971550          # Coloque o seu ID do Discord aqui
CARGO_SUPORTE_ID = 1529832924612923422 # Coloque o ID do Cargo de Suporte aqui
# =================================================

DATABASE_KEYS = {}
SERVIDORES_ATIVADOS = {}

# --- MODAL PARA GERAR A KEY ---
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

# --- MODAL PARA CANCELAR A KEY ---
class ModalCancelarKey(discord.ui.Modal, title="Cancelar Key"):
    chave = discord.ui.TextInput(label="Digite a key que quer cancelar", placeholder="Cole a key aqui...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        key_digitada = self.chave.value.strip()
        if key_digitada in DATABASE_KEYS:
            del DATABASE_KEYS[key_digitada]
            await interaction.response.send_message(f"🗑️ A key `{key_digitada}` foi cancelada!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Key não encontrada!", ephemeral=True)

# --- PAINEL DE KEYS ---
class PainelKeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Gerar Key", style=discord.ButtonStyle.green, custom_id="btn_gerar_key")
    async def gerar_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != MEU_ID:
            await interaction.response.send_message("❌ Apenas o dono!", ephemeral=True)
            return
        await interaction.response.send_modal(ModalGerarKey())

    @discord.ui.button(label="Ver Keys", style=discord.ButtonStyle.blurple, custom_id="btn_ver_key")
    async def ver_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != MEU_ID:
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
        if interaction.user.id != MEU_ID:
            await interaction.response.send_message("❌ Apenas o dono!", ephemeral=True)
            return
        await interaction.response.send_modal(ModalCancelarKey())


# --- MODAL PARA RENOMEAR O TICKET ---
class ModalRenomearTicket(discord.ui.Modal, title="Renomear Ticket"):
    novo_nome = discord.ui.TextInput(label="Novo nome do canal", placeholder="Ex: atendimento-nome", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.edit(name=self.novo_nome.value)
        await interaction.response.send_message(f"✅ Canal renomeado para: **{self.novo_nome.value}**", ephemeral=True)


# --- BOTÕES DENTRO DO TICKET (PERSISTENTES) ---
class TicketControlesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assumir por ninguém", style=discord.ButtonStyle.primary, emoji="🛠️", custom_id="ticket_assumir")
    async def assumir(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verifica se quem clicou tem o cargo de suporte ou é admin
        tem_cargo = any(r.id == CARGO_SUPORTE_ID for r in interaction.user.roles)
        if not tem_cargo and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas membros da equipe de suporte podem assumir o ticket!", ephemeral=True)
            return

        button.label = f"Assumido por {interaction.user.display_name}"
        button.style = discord.ButtonStyle.success
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"✅ Ticket assumido por {interaction.user.mention}!")

    @discord.ui.button(label="Renomear", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="ticket_renomear")
    async def renomear(self, interaction: discord.Interaction, button: discord.ui.Button):
        tem_cargo = any(r.id == CARGO_SUPORTE_ID for r in interaction.user.roles)
        if not tem_cargo and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas a equipe pode renomear!", ephemeral=True)
            return
        await interaction.response.send_modal(ModalRenomearTicket())

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="✖️", custom_id="ticket_cancelar")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fechando ticket em 3 segundos...", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_fechar")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fechando ticket em 3 segundos...", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.channel.delete()


# --- MENU SUSPENSO DE CATEGORIAS ---
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="DÚVIDAS", description="Tire suas dúvidas aqui!", emoji="🛠️"),
            discord.SelectOption(label="ENTRAR NA EQUIPE", description="Entre na nossa equipe", emoji="📝"),
            discord.SelectOption(label="SEJA AFILIADO", description="Seja afiliado e ganhe seu dinheiro", emoji="💰"),
            discord.SelectOption(label="PARCERIA", description="Abrir ticket: PARCERIA", emoji="🤝")
        ]
        super().__init__(placeholder="Selecione a categoria do ticket...", min_values=1, max_values=1, options=options, custom_id="persistent_ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        categoria_escolhida = self.values[0]

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"❌ Você já possui um ticket aberto em {existing_channel.mention}!", ephemeral=True)
            return

        cargo_suporte = guild.get_role(CARGO_SUPORTE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        if cargo_suporte:
            overwrites[cargo_suporte] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ticket_channel = await guild.create_text_channel(name=f"ticket-{member.name}", overwrites=overwrites)
        
        await interaction.response.send_message(f"✅ Seu ticket foi criado com sucesso em {ticket_channel.mention}!", ephemeral=True)
        
        mencao_suporte = cargo_suporte.mention if cargo_suporte else "@everyone"
        
        embed = discord.Embed(
            title=f"🛠️ Ticket — {categoria_escolhida}",
            description=f"{member.mention} Envie sua dúvida aqui e nossa equipe já te responde!",
            color=discord.Color.gold()
        )
        embed.add_field(name="👤 Usuário", value=f"{member.mention}\n({member.name})", inline=False)
        embed.add_field(name="📁 Categoria", value=f"🛠️ {categoria_escolhida}", inline=False)
        embed.set_footer(text="Equipe de Suporte • Responderemos em breve")

        await ticket_channel.send(content=f"{member.mention} {mencao_suporte}", embed=embed, view=TicketControlesView())

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


@bot.event
async def on_ready():
    bot.add_view(PainelKeyView())
    bot.add_view(TicketView())
    bot.add_view(TicketControlesView())
    print(f'Bot conectado como {bot.user.name} e Views Persistentes ativadas!')

# --- COMANDOS DE KEYS ---
@bot.command(name="criar-key")
async def criar_key(ctx):
    if ctx.author.id != MEU_ID and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Apenas o dono pode usar este comando!")
        return
    
    embed = discord.Embed(title="Painel de Keys", description="Use os botões abaixo:", color=discord.Color.gold())
    await ctx.send(embed=embed, view=PainelKeyView())

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

# --- COMANDO !PAINEL ---
@bot.command(name="painel")
async def painel(ctx):
    if ctx.guild.id not in SERVIDORES_ATIVADOS:
        await ctx.send("⚠️ Coloque sua key em `!ativar <sua_key>` antes de usar este comando!")
        return

    embed = discord.Embed(
        title="👑 SISTEMA DE ATENDIMENTO",
        description=(
            "👑 Na Infinity Systems, estamos sempre prontos para ajudar você.\n\n"
            "⚡ Ficou com alguma dúvida?\n"
            "Abra um ticket selecionando a categoria abaixo e nos conte o que precisa — nossa equipe irá te auxiliar da melhor forma possível.\n\n"
            "⚡ **Horário de Atendimento:**\n"
            "Segunda a sexta, das 13:30 às 23:00.\n"
            "Sábado e domingo das 08:00 às 20:00.\n\n"
            "Equipe de Suporte"
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=TicketView())

bot.run("DISCORD_TOKEN")
