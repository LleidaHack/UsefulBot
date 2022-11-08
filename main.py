# bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from datetime import datetime,date

import Config

YEAR='2022'
cred = credentials.Certificate(Config.DB_CERT)
firebase_admin.initialize_app(cred)
db = firestore.client()


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
async def allergies_more(ctx, yr=YEAR):
  users = get_users(yr)
  al={'vegetaria':0, 'vega':0, 'gluten':0, 'lactosa':0}
  for us in users:
    u = us.to_dict()
    if u['food'] != '':
      if u['food'].capitalize().contains('Vegetaria'.capitalize()):
        al['vegetaria']+=1
      if u['food'].capitalize().contains('Vega'.capitalize()):
        al['vega']+=1
      if u['food'].capitalize().contains('Gluten'.capitalize()):
        al['gluten']+=1
      if u['food'].capitalize().contains('Lactosa'.capitalize()):
        al['lactosa']+=1
  await ctx.send('ALERGY DATA:')
  await ctx.send('vegetarian: ' + str(al['vegetaria']))
  await ctx.send('vegan: ' + str(al['vega']))
  await ctx.send('gluten: ' + str(al['gluten']))
  await ctx.send('lactosa: ' + str(al['lactosa']))

def get_users(yr):
  users_ref = db.collection('hackeps-' + str(yr) + '/prod/users')
  return users_ref.stream()

def get_teams(yr):
  teams_ref = db.collection('hackeps-' + str(yr) + '/prod/teams')
  return teams_ref.stream()

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

bot.run(Config.TOKEN)
