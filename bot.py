import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

SUPPORT_ROLE_ID = 1529555873960038520  

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="DÚVIDAS", description="TIRE SUAS DÚVIDAS AQUI!", emoji="🛠️", value="duvidas"),
            discord.SelectOption(label="ENTRAR NA EQUIPE", description="ENTRE NA NOSSA EQUIPE", emoji="📝", value="equipe"),
            discord.SelectOption(label="SEJA AFILIADO", description="SEJA AFILIADO E GANHE SEU DINHEIRO", emoji="👛", value="afiliado"),
            discord.SelectOption(label="PARCERIA", description="Abrir ticket: PARCERIA", emoji="🤝", value="parceria")
        ]
        super().__init__(placeholder="🛠️ DÚVIDAS", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        category_name = self.values[0].upper()
        channel_name = f"ticket-{interaction.user.name}-{category_name.lower()}"
        
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🛠️ Ticket — {category_name}",
            description=f"{interaction.user.mention} Envie sua dúvida aqui e nossa equipe já te responde!",
            color=discord.Color.gold()
        )
        embed.add_field(name="👤 Usuário", value=f"{interaction.user.mention}\n(`{interaction.user.name}`)", inline=False)
        embed.add_field(name="📁 Categoria", value=f"🛠️ {category_name}", inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Equipe de Suporte • Responderemos em breve")

        view = TicketControlView()
        await ticket_channel.send(content=f"{interaction.user.mention} | {support_role.mention if support_role else ''}", embed=embed, view=view)
        await interaction.response.send_message(f"Seu ticket foi criado com sucesso: {ticket_channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assumido por ninguém", style=discord.ButtonStyle.blurple, emoji="🛠️", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.label = f"Assumido por {interaction.user.name}"
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"Este ticket foi assumido por {interaction.user.mention}.", ephemeral=False)

    @discord.ui.button(label="Renomear", style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="rename_ticket")
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Comando de renomear acionado.", ephemeral=True)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="cancel_ticket")
    async def cancel_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Fechando ticket em instantes...", ephemeral=True)
        await interaction.channel.delete()

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.gray, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("O ticket está sendo encerrado.", ephemeral=True)
        await interaction.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def painel(ctx):
    embed = discord.Embed(
        title="👑 SISTEMA DE ATENDIMENTO",
        description="👑 Na Infinity Systems, estamos sempre prontos para ajudar você.\n\n"
                    "> ⚡ Ficou com alguma dúvida?\n"
                    "> Abra um ticket selecionando a categoria abaixo e nos conte o que precisa — nossa equipe irá te auxiliar da melhor forma possível.\n\n"
                    "⚡ **Horário de Atendimento:**\nSegunda a sexta, das 08:00 às 23:00.\nSábado e domingo das 08:00 às 20:00.",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Equipe de Suporte")
    
    view = TicketView()
    await ctx.send(embed=embed, view=view)

@bot.command(name="pix")
async def pix(ctx):
    # 1. Coloque o SEU ID de usuário aqui
    meu_id = 1474550396813971550
    
    # 2. Coloque o ID DO CARGO de vendedor aqui
    cargo_vendedor_id = 1522730037223096561

    # Verifica se a pessoa tem o cargo de vendedor
    tem_cargo = any(role.id == cargo_vendedor_id for role in ctx.author.roles)
    
    # Autoriza se for você, se tiver o cargo, ou se for administrador
    eh_autorizado = (ctx.author.id == meu_id) or tem_cargo or ctx.author.guild_permissions.administrator
    
    if not eh_autorizado:
        await ctx.send("Somente os donos e os vendedores conseguirão usar!")
        return

    embed = discord.Embed(
        title="CHAVE PIX DONO",
        description=(
            "**TIPO DE CHAVE:** C121d5b0-36f9-4fa6-9590-916db7848b5b\n\n"
            "**NOME:** JOÃO PEDRO GOMES DE SOUSA\n\n"
            "**PIX:** C121d5b0-36f9-4fa6-9590-916db7848b5b\n\n"
            "**INSTITUIÇÃO:** Nubank"
        ),
        color=discord.Color.green()
    )
    
    # Coloca a foto no canto superior direito
    embed.set_thumbnail(url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot logado como {bot.user}!")

bot.run(os.getenv("DISCORD_TOKEN"))
