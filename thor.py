import discord
from discord.ext.commands import Bot
from discord import Game
import sqlite3
import aiosqlite
import antispam
import json

class ServersDatabase:

    def __init__(self):
        self.db = sqlite3.connect('Thor.db')
        self.db2 = sqlite3.connect('ThorSpamDataset.db')
        self.cursor2 = self.db2.cursor()
        self.cursor2.execute("CREATE TABLE IF NOT EXISTS DiscordGeneralSpam(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, spam_text TEXT);")
        self.cursor = self.db.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS DiscordServers(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, servername TEXT, serverid INTEGER, configuration TEXT, users TEXT, UNIQUE(serverid));")
        self.db.commit()
        self.db2.commit()


    async def register_server(self, svname, svid):
        print("Trying to register: {0}, {1}".format(svname, svid))
        async with aiosqlite.connect('Thor.db') as db:
            cursor = await db.execute('SELECT serverid FROM DiscordServers WHERE serverid=(?)',(int(svid), ) )
            result = await cursor.fetchone()
            await cursor.close()
            if result == None:
                await db.execute('INSERT INTO DiscordServers(servername, serverid) VALUES(?, ?)', (str(svname), int(svid), ))
                await db.commit()
                return True
                print("Registered")
            else:
                return False

    async def register_users(self, server, client=None):
        print("Saving usernames from server into database, safe users")
        async with aiosqlite.server_configurationconnect('Thor.db') as db:
            cursor = await db.execute('SELECT serverid FROM DiscordServers WHERE serverid=(?)',(int(server.id), ) )
            result = await cursor.fetchone()
            if result == None:
                pass
            else:
                users = server.members
                userdb = {"usernames":[], "userid":[]}
                for i in users:
                    userdb["usernames"].append(i.display_name)
                    userdb["userid"].append(str(i.id))
                result_to_save = json.dumps(userdb)
                if client != server_configurationNone:
                    await client.say("Obrigado por registrar o servidor na proteção divina de Asgard!")
                    await client.say("Para melhorar a segurança, esses nomes de usuário serão lembrados como seguros para acessar aqui")

                    usuarios = json.loads(result_to_save)

                    mensagem = "\n"
                    for c in usuarios["usernames"]:
                        mensagem += c.strip()
                        mensagem += '\n'
                    await client.say("```{0}```".format(mensagem))
                cursor = await db.execute('UPDATE DiscordServers SET users=? WHERE serverid=(?)',(str(result_to_save), int(server.id), ))
                await cursor.close()
                await db.commit()

    async def Add_Spam(self, spam_message, user, server):
        async with aiosqlite.connect('ThorSpamDataset.db') as db:
            cursor = await db.execute('INSERT INTO DiscordGeneralSpam(spam_text) VALUES(?)', (spam_message, ))
            await cursor.close()
            await db.commit()
            print("[{0}][{1}] Marked [{2}] as spam".format(server.name,user.display_name,json.loads(spam_message)["spam"][0]))

    async def Train_Thor(self):
        async with aiosqlite.connect('ThorSpamDataset.db') as db:
            cursor = await db.execute('SELECT spam_text FROM DiscordGeneralSpam')
            data = await cursor.fetchall()
            spam_data = []
            for i in data:
                spam_data.append(json.loads(i[0]))
            print("[AVISO] Thor em treinamento!")
            model = antispam.Model('ThorModel.dat', False)
            d = antispam.Detector('ThorModel.dat', False)
            for i in spam_data:
                d.train(str(i['spam'][0]), True)
            d.save()
            print("[AVISO] Thor terminou o treinamento")
            # for i in spam_data:
            #     i = json.loads(i)["spam"]
            #     model.train(i, True)

    async def check_server(self,svid):
        self.cursor.execute('SELECT servername FROM DiscordServers WHERE serverid=(?)', (int(svid), ) )
        return self.cursor.fetchone()[0]

    async def check_blacklist(self, name):
        async with aiosqlite.connect('ThorSpamDataset.db') as db:
            cursor = await db.execute('SELECT spam_text FROM DiscordGeneralSpam WHERE spam_text=(?)',(str(name), ) )
            result = await cursor.fetchone()
            if result == None:
                return False
            else:
                return True

    async def get_configuration(self, server):
        async with aiosqlite.connect('Thor.db') as db:
            cursor = await db.execute('SELECT server_configuration FROM DiscordServers WHERE serverid=(?)',(int(server.id), ) )
            result = await cursor.fetchone()
            if result != None:
                return result[0]
            return None

    async def insert_configuration(self, server, config):
        async with aiosqlite.connect('Thor.db') as db:
            cursor = await db.execute('SELECT serverid FROM DiscordServers WHERE serverid=(?)',(int(server.id), ) )
            result = await cursor.fetchone()
            if result != None:
                cursor = await db.execute('UPDATE DiscordServers SET server_configuration=? WHERE serverid=(?)',(str(config), int(server.id), ))


config = open("config.data", "r")
data = None
try:
    for line in config:
        data = json.loads(line)
        break
except FileNotFoundError:
    print("Config file not found!")
    print("Format ==> {'TOKEN':'abc'}")
    exit()
TOKEN = data["TOKEN"]



BOT_PREFIX = ("!")
client = Bot(command_prefix=BOT_PREFIX)
database = ServersDatabase()
announce_channel = "thor"
configuration = {"announce_channel":"thor", "pm_message":"message", "ban_wait":3, "kick_wait":1}

@client.command(name="myid", pass_context=True)
async def getid(ctx):
    await client.say("```{0}```".format(ctx.message.author.id))

@client.command(name="Scan_server", pass_context=True, brief="Escaneia o servidor em busca de bots spam", aliases=["scan_server"])
async def scan(ctx):
    if ctx.message.channel.permissions_for(ctx.message.author).administrator:
        probs = {"users":[], "probability":[]}
        for user in ctx.message.author.server.members:
            probs["users"].append(user.display_name)
            p = await NickSpamHeuristic(nick=user.display_name)
            probs["probability"].append(p*100)
        msg = "\n"
        for i in range(len(probs["users"])):
            msg += "{0} ==> {1}".format(probs["users"][i], str(probs["probability"][i]))
            msg += '\n'
        await client.say("```"+msg+"```")
    else:
        await client.say("A mensagem é tão poderosa que apenas verdadeiros guerreiros podem a ler!")

@client.command(name='treinar', description="Somente os dignos podem forjar novas armas contra o spam", brief="Treina o thor baseado em novas informações", pass_context=True)
async def train_thor(ctx):
    if str(ctx.message.author.id) == str(256153166582775812):
        await client.say("Ta saindo da jaula o monstro! ```BIRRRRLL```")
        await database.Train_Thor()
    else:
        await client.say("Somente os anões de Nidavellir podem forjar novas armas místicas")

@client.command(name='heimdall', pass_context=True, brief="Mostrar a quais reinos o Thor está vigiando")
async def show_servers(ctx):
    sv = client.servers
    servers = ""
    for i in sv:
        servers += i.name
        servers += '\n'

    await client.say("Eu estou a vigiar: ```{0}```".format(servers))

@client.command(name='listar_canais', pass_context = True, brief="Mostrar os canais em que possuo permissão de escrita")
async def show_channels(ctx):
    list = ""
    server = ctx.message.author.server
    for channel in server.channels:
        if channel.type == discord.ChannelType.text:
            # Channels on the server
            if channel.permissions_for(server.me).send_messages:
                list += channel.name
                list += "\n"

    await client.say("Eu vou anunciar coisas como novos usuários em um canal especial chamado %s, caso esse canal não exista, não irei anunciar nada"%announce_channel)
    existe = False
    sv = ctx.message.author.server
    for channel in sv.channels:
        if channel.type == discord.ChannelType.text:
            # Channels on the server
            if channel.permissions_for(sv.me).send_messages:
                if channel.name == announce_channel:
                    existe = True

    msg = "não existe"
    if existe:
            msg = "existe"

    await client.say("E este canal... ```{0}```".format(msg))
    await client.say("Eu tenho acesso a escrita em: ```{0}``` nesses canais eu posso responder coisas a quem me perguntar".format(list))

@client.command(name='t_help', pass_context = True, aliases=["t_Ajuda", "t_ajuda", "t_Help"], brief="Mostrar este diálogo de ajuda")
async def show_help(ctx):
    await client.say("Olá {}, EU SOU THOR, portador do BANHAMMER, filho de STKzica".format(ctx.message.author.display_name))
    await client.say("Eu estou neste universo com o único objetivo de deter os robôs do ultron")
    await client.say("E é isso que eu faço, não muito bem por enquanto, mas assim que meu machado estiver pronto eu vou comer o cu deles")
    await client.say("https://www.einerd.com.br/wp-content/uploads/2018/03/vingadores-guerra-infinita-novo-trailer-9.jpg")
    text = open('commands.txt','r')
    lines = text.readlines()

    commands = []
    for i in client.walk_commands():
        dup = False
        for j in range(len(commands)):
            if commands[j] == i:
                dup = True
                break
        if dup == False:
            commands.append(i)
    text = ""
    for i in commands:
        text += "{0} : {1}".format(i.name, i.brief)
        text += '\n'

    help = "Thor Commands: ```{0}```".format(text)
    await client.say(help)


@client.command(name='permissions', pass_context = True, brief='Mostrar permissões do usuário')
async def show_permissions(context):
    member = context.message.author
    channel = context.message.channel
    await client.say("These are all the permissions for %s"%member.display_name)
    for i in member.server_permissions:
        await client.say("```"+str(i)+"```")

@client.command(name='iamgod', pass_context = True, brief='Checar se o usuário é admin')
async def yougod(context):
    channel = context.message.channel
    if channel.permissions_for(context.message.author).administrator:
        await client.say("Parece que tu és poderoso como eu, qual shampoo tu usas?")
    else:
        await client.say("Seu cabelo é ruim como bombrill")



@client.command(name='registrar_servidor', pass_context = True, brief="Registra o servidor na proteção divina")
async def register_server(context):
    member = context.message.author
    await client.say("Tentativa de registrar %s no banco de dados"%member.server.name)
    registered = await database.register_server(svname=member.server.name,svid=member.server.id)
    if(registered):
        print("New server under protection: %s"%context.message.author.server.name)
        await client.say("Registrado com sucesso")
        await database.register_users(server=context.message.author.server, client=client)
    else:
        await client.say("O servidor já se encontra sob proteção divina")

@client.command(name='probability', pass_context = True, brief="The probability of the thing being a spam")
async def probability(ctx):
    msg = ctx.message.content.replace("!probability","").strip()
    if len(msg) > 2:
        prob = await NickSpamHeuristic(msg)
        prob = prob*100
        await client.say("Olá, de acordo com a inteligência asgardiana, a probabilidade de [{0}] ser spam é de: ```{1}```".format(msg, str(prob)))
    else:
        await client.say("Eu quero é que você me explique como que alguém anuncia com isso")

@client.command(name='propósito',
                description='Proprósito do bot',
                brief='O propósito do Deus do martelo do BAN',
                aliases=['bot_purpose'],
                pass_context = True)
async def bot_putpose(context):
    await client.say("Enquanto eu respirar, spam tu não farás")


@client.command(name='Spam_nick',
                description='Apontar algum nome como spam',
                brief='Me ajude a saber quem é spammer',
                aliases=['spam_nick'],
                pass_context = True)
async def Spam(context):
    msg = context.message.content
    msg = msg.replace("!Spam_nick","").replace("!spam_nick","").strip()
    spam = {"spam":[]}
    spam["spam"].append(msg)
    try:
        await database.Add_Spam(user=context.message.author,server=context.message.author.server, spam_message=json.dumps(spam))
        await client.say("Os guerreiros de Asgard agora veem [%s] com hostilidade!"%msg)
    except OperationalError:
        await clietn.say("Aparentemente eu estou ocupado lutando com Thanos, tente novamente jájá")
@client.command(name='teste', brief="Verifica se o bot está vivo")
async def teste():
    await client.say("Estou vivo e pronto para combate!")

@client.command(name="lista_alerta", brief="A quem vou reportar problemas no servidor", pass_context = True)
async def alertar(ctx):
    server = ctx.message.author.server
    members = server.members
    message = "\n"

    for i in members:
        if ctx.message.channel.permissions_for(i).administrator and not i.bot:
            message += i.display_name
            message += '\n'
    await client.say("Vou alertar a esses admins se eu resolver largar o dedo em alguém: ```%s```"%message)

@client.command(name="configurar_thor", brief="O peso de meu martelo quem determina é você", pass_context = True)
async def config_ban(ctx):
    configuration = {"announce_channel":"thor", "pm_message":"message", "ban_wait":3, "kick_wait":1}

    if ctx.message.channel.permissions_for(ctx.message.author).administrator:
        config = await database.get_configuration(server=ctx.message.author.server)
        if config:
            configuration = config
        msg = "Essas são minhas configurações atuais, caro guerreiro"
        msg2 = "```{0}```".format(json.dumps(configuration))
        await client.say(msg+'\n'+msg2)
        umsg = ctx.message.content.replace("!configurar_thor","").strip().lower()
        newconfiguration = configuration

        if len(umsg.strip("announce_channel")) > 1:
            newconfiguration["announce_channel"] = str(umsg).replace("announce_channel", "").strip()
            await client.say("Configurações salvas")

        elif len(umsg.strip("pm_message")) > 1:
            newconfiguration["pm_message"] = str(umsg).replace("pm_message", "").strip()
            await client.say("Configurações salvas")
        elif len(umsg.strip("ban_wait")) > 1:
            try:
                newconfiguration["ban_wait"] = int(str(umsg).replace("ban_wait", "").strip())
                await client.say("Configurações salvas")
            except:
                await client.say("Eu preciso de um número de tentativas, não %s"%umsg.replace("ban_wait","").strip())

        elif len(umsg.replace("kick_wait")) > 1:
            try:
                newconfiguration["kick_wait"] = int(str(umsg).replace("kick_wait", "").strip())
                await client.say("Configurações salvas")
            except:
                await client.say("Eu preciso de um número de tentativas, não %s"%umsg.replace("ban_wait","").strip())
    else:
        await client.say("Você não é digno de empunhar meu martelo")

@client.event
async def on_ready():
    await client.change_presence(game=Game(name="BANHAMMER"))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print("******SERVERS*******")
    for i in client.servers:
        print(i.name)
    print("*************")
    print('------')

@client.event
async def on_member_join(member):
    spammer = False
    classfier = False

    blacklist = await database.check_blacklist(member.display_name)
    prob = await NickSpamHeuristic(member.display_name)
    if (ValidName(member.display_name) and not blacklist):
        if not prob > 0.9:
            guild = member.server
            for channel in guild.channels:
                if channel.type == discord.ChannelType.text:
                    # Channels on the server
                    if channel.permissions_for(guild.me).send_messages:
                        if channel.name == announce_channel:
                            print("[{0}] entrou no servidor [{1}]".format(member.display_name, member.server.name))
                            await client.send_message(channel, "[{0}] Se juntou a nós\n```[{1}]```".format(member.mention, prob*100))
                            break
        else:
            classfier = True
            spammer = True
    else:
        spammer = True
    if spammer and classfier:
        print("----%s-----"%member.server.name)
        print("[INFO][CLASSFIER] SPAMMER JOINED >> {0}".format(member.display_name))
        print("-----------")
    else:
        print("----%s-----"%member.server.name)
        print("[INFO] SPAMMER JOINED >> {0}".format(member.display_name))
        print("-----------")

@client.event
async def on_member_remove(member):
    spammer = False
    classfier = False
    blacklist = await database.check_blacklist(member.display_name)
    prob = await NickSpamHeuristic(member.display_name)
    if (ValidName(member.display_name) and not blacklist):
        if not prob > 0.9:
            guild = member.server
            for channel in guild.channels:
                if channel.type == discord.ChannelType.text:
                    # Channels on the server
                    if channel.permissions_for(guild.me).send_messages:
                        if channel.name == announce_channel:
                            print("[{0}] saiu do servidor [{1}]".format(member.display_name, member.server.name))
                            await client.send_message(channel, "[{}] fugiu".format(member.display_name))
                            break
        else:
            classfier = True
            spammer = True
    else:
        spammer = True
    if spammer and classfier:
        print("----%s-----"%member.server.name)
        print("[INFO][CLASSFIER] SPAMMER LEFT >> {0}".format(member.display_name))
        print("-----------")
    else:
        print("----%s-----"%member.server.name)
        print("[INFO] SPAMMER LEFT >> {0}".format(member.display_name))
        print("-----------")
@client.event
async def on_member_update(before, after):
    name = before.display_name
    prob1 = await NickSpamHeuristic(before.display_name)
    prob2 = await NickSpamHeuristic(after.display_name)
    spam = False
    if (prob1 > 0.9 or prob2 > 0.9):
        spam = True

    if ValidName(before.display_name) and ValidName(after.display_name) and not spam:
        if before.nick != after.nick:
            sv = before.server
            for channel in sv.channels:
                if channel.type == discord.ChannelType.text:
                    # Channels on the server
                    if channel.permissions_for(sv.me).send_messages:
                        if channel.name == announce_channel:
                            print("[INFO][{0}] {1} [>>>] {2}".format(before.server.name, before.display_name, after.display_name))
                            await client.send_message(channel, "{0} [>>>] {1}".format(before.display_name, after.display_name))
                            break
        else:
            pass
            # print("[INFO][{0}] Usuário modificado -> [{1}]".format(before.server.name, before.display_name))
            #await client.send_message(after, "Meus olhos estão em você, {}, meu martelo anseia pela sua destruição".format(name))
    else:
        print("Detected spammer: {0}".format(after.display_name))
        if (prob1 != prob2):
            sv = before.server
            for channel in sv.channels:
                if channel.type == discord.ChannelType.text:
                    # Channels on the server
                    if channel.permissions_for(sv.me).send_messages:
                        if channel.name == announce_channel:
                            for i in sv.members:
                                if not i.bot:
                                    if channel.permissions_for(i).administrator:
                                        print("Alertando: %s"%i.display_name)
                                        await client.send_message(i, "Olá caro {0}, Temos um infiltrado!\nLhe envio este manifesto com o alerta! ```{1} [>>>] {2}```\nPossível candidato a kick/ban".format(i.mention, before.display_name, after.display_name))
                                        await client.send_message(i, "```{0} ==> {1}```".format(str(prob1*100), str(prob2*100)))
                            break
def ValidName(name):
    #Feito para impedir anuncio de links no nome
    link = "http"
    if len(name.split(link)) > 1:
        return False
    else:
        return True

async def NickSpamHeuristic(nick):
    model = antispam.Detector('ThorModel.dat', False)
    try:
        return model.score(nick)
    except TypeError:
        return 0
client.run(TOKEN)
