import telebot
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

# (Кэш)
active_sessions = {}      
reg_cache = {}            
user_filters = {}         
payment_cache = {}        
donation_cache = {}       
admin_action_cache = {}   
