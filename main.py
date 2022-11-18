# bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime,date

import Config

YEAR='2022'
ENV='prod'
cred = credentials.Certificate(Config.DB_CERT)
firebase_admin.initialize_app(cred)
db = firestore.client()


def init_drive(): 
  scope = ['https://spreadsheets.google.com/feeds',
           'https://www.googleapis.com/auth/drive']
  creds = ServiceAccountCredentials.from_json_keyfile_name(Config.CLIENT_KEY, scope)
  client = gspread.authorize(creds)
  return client

client=init_drive()
sheet=spreadsheet = client.open("USERS")

bot = commands.Bot(command_prefix='!')

def age(birthdate):
    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

@bot.command()
async def users(ctx, yr=YEAR):
  usrs = get_users(yr)
  i=0
  for u in usrs:
    i+=1
  await ctx.send("users(" + str(yr) + ")  ->  " + str(i))

@bot.command()
async def assisted(ctx, yr=YEAR):
  users = get_users(yr)
  i=0
  for us in users:
    u=us.to_dict()
    try:
      if u['registered'] == True:
        i+=1
    except:
      pass
  await ctx.send("assisted(" + str(yr) + ")  ->  " + str(i))

@bot.command()
async def teams(ctx, yr=YEAR):
  tms = get_teams(yr)
  i=0
  for t in tms:
    i+=1
  await ctx.send("teams(" + str(yr) + ")  ->  " + str(i))

@bot.command()
async def sizes(ctx, yr=YEAR):
  users = get_users(yr)
  sizes = {}
  for us in users:
    u=us.to_dict()
    s=u['shirtSize']
    if s in sizes:
      sizes[s]+=1
    else:
      sizes[s]=1
  out = "Sizes(" + str(yr) + "):\n"
  for k, v in sizes.items():
    out += "\t" + k + " ---> " + str(v) + "\n"
  await ctx.send(out)

@bot.command()
async def accepted(ctx, yr=YEAR):
  users = get_users(yr)
  i=0
  for us in users:
    u = us.to_dict()
    if u['accepted'] == 'YES':
      i+=1
  await ctx.send('Accepted users(' + str(yr) + ')  ->  ' + str(i))

@bot.command()
async def accepted_mails(ctx, yr=YEAR):
  users = get_users(yr)
  await ctx.author.send('EMAILS:')
  for us in users:
    u = us.to_dict()
    if u['accepted'] == 'YES':
      await ctx.author.send("\t" + u['email'])
  await ctx.send("Done :)")

@bot.command()
async def minors(ctx, yr=YEAR):
  users = get_users(yr)
  i=0
  for us in users:
    u = us.to_dict()
    if age(datetime.strptime(u["birthDate"], '%Y-%m-%d').date()) < 18:
      i+=1
  await ctx.send('Minors(' + str(yr) + ')  ->  ' + str(i))

@bot.command()
async def minors_data(ctx, yr=YEAR):
  users = get_users(yr)
  await ctx.author.send('MINORS DATA:')
  for us in users:
    u = us.to_dict()
    if age(datetime.strptime(u['birthDate'], '%Y-%m-%d').date()) < 18:
      await ctx.author.send(f"{u['fullName']} - {u['birthDate']} - {age(datetime.strptime(u['birthDate'], '%Y-%m-%d'))} - {u['email']}")
  await ctx.send('Done :)')

@bot.command()
async def allergies(ctx, yr=YEAR):
  users = get_users(yr)
  await ctx.author.send('ALERGY DATA:')
  for us in users:
    u = us.to_dict()
    if u['food'] != '':
      await ctx.author.send(f"{u['fullName']} - {u['food']}")
  await ctx.send('Done :)')

@bot.command()
async def users_no_team(ctx, yr=YEAR):
  teams = [t.to_dict()['members'] for t in get_teams(YEAR)]
  teamMembers = [m.get().id for t in teams for m in t]
  usersId = [u.to_dict()['uid'] for u in get_users(YEAR)]
  usersWithoutTeamId = [u for u in usersId if u not in teamMembers]
  await ctx.send('Users with no team('+yr+')  ->  '+str(len(usersWithoutTeamId)))

@bot.command()
async def allergies_more(ctx, yr=YEAR):
  users = get_users(yr)
  al={'vegetaria':0, 'vega':0, 'gluten':0, 'lactosa':0}
  for us in users:
    u = us.to_dict()
    if u['food'] != '':
      if 'vegetaria'.upper() in u['food'].upper():
        al['vegetaria']+=1
      if 'vega'.upper() in u['food'].upper():
        al['vega']+=1
      if 'gluten'.upper() in u['food'].upper():
        al['gluten']+=1
      if 'lactosa'.upper() in u['food'].upper():
        al['lactosa']+=1
  await ctx.send('ALERGY DATA:')
  await ctx.send('vegetarian: ' + str(al['vegetaria']))
  await ctx.send('vegan: ' + str(al['vega']))
  await ctx.send('gluten: ' + str(al['gluten']))
  await ctx.send('lactose: ' + str(al['lactosa']))

@bot.command()
async def search(ctx, data, yr=YEAR):
  usr_data=''
  if '@' in data:
    usr_data = get_user_by_email(data, yr)
  else:
    usr_data = get_user_by_uid(data, yr)
  if usr_data == None:
    await ctx.send('User not found')
  else:
    await ctx.send(usr_data.to_dict())

@bot.command()
async def unregister(ctx, uid, yr=YEAR):
  usr_data = get_user_by_uid(uid, yr)
  if usr_data == None:
    await ctx.send('User not found')
  else:
    #delete registered field
    usr_data.reference.update({'registered': firestore.DELETE_FIELD})
    await ctx.send('User unregistered')

@bot.command()
async def update(ctx,yr=YEAR):
  users = get_users(yr)
  definition = get_definition(yr)
  #get uids from excel
  uids = [e[0] for e in sheet.worksheet(YEAR).get_all_values()]
  for us in users:
    u = us.to_dict()
    if not u['uid'] in uids:
      #add user to excel
      row = []
      for key in definition:
          try:
              row.append(u[key])
          except:
              row.append('')
      sheet.worksheet(YEAR).append_row(row)

def get_definition(yr):
    user=list(get_users(yr)[0].keys())
    user.insert(0, user.pop(user.index('uid')))
    user.insert(1, user.pop(user.index('fullName')))
    user.insert(2, user.pop(user.index('email')))
    user.insert(3, user.pop(user.index('birthDate')))
    user.insert(len(user)-1, user.pop(user.index('food')))
    user.insert(len(user)-1, user.pop(user.index('accepted')))
    user.insert(len(user)-1, user.pop(user.index('gdpr')))
    user.insert(len(user)-1, user.pop(user.index('terms')))
    user.insert(len(user)-1, user.pop(user.index('githubUrl')))
    user.insert(len(user)-1, user.pop(user.index('linkedinUrl')))
    user.insert(len(user)-1, user.pop(user.index('photoURL')))
    return user

def get_user_by_uid(uid, yr=YEAR):
  users = get_users(yr)
  for us in users:
    u = us.to_dict()
    if u['uid'] == uid:
      return us
  return None

def get_user_by_email(email, yr=YEAR):
  users = get_users(yr)
  for u in users:
    if u.to_dict()['email'] == email:
      return u
  return None

def get_users(yr):
  users_ref = db.collection('hackeps-' + str(yr) + '/' + ENV + '/users')
  return users_ref.stream()

def get_teams(yr):
  teams_ref = db.collection('hackeps-' + str(yr) + '/' + ENV + '/teams')
  return teams_ref.stream()

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

bot.run(Config.TOKEN)
