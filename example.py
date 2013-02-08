#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import cgi
import datetime
import urllib
import wsgiref.handlers
from operator import itemgetter, attrgetter

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

##os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
##
##from google.appengine.dist import use_library
##use_library('django', '1.2')

from google.appengine.api import users

from google.appengine.api import mail

import res


#class Greeting(db.Model):
#	"""Models an individual Guestbook entry with an author, content, and date."""
#	author = db.UserProperty()
#	content = db.StringProperty(multiline=True)
#	date = db.DateTimeProperty(auto_now_add=True)
#	room = db.StringProperty()

class MainPage(webapp.RequestHandler):
	def get(self):
		room=self.request.get('room')
		maxComment=self.request.get('maxcm')
		if not maxComment: maxComment=8
		else:maxComment=int(maxComment)
		#greetings_query = Greeting.all().ancestor(guestbook_key(guestbook_name)).order('-date')
		
		greetings_query = db.GqlQuery("SELECT * FROM Greeting Where room=:1 ORDER BY date DESC",room)
		data = greetings_query.fetch(maxComment)
		#data=sorted(data, key=attrgetter('date'))
		
		#greetings=data[-maxComment:]
		#leftComment=len(data)-maxComment
		greetings=reversed(data);
		leftComment=0;
		
		if leftComment < 0 : leftComment=0
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		
		#date refix
		#		td7=datetime.timedelta(hours=7)
		#		for gr in greetings:
		#			gr.date=gr.date+td7
		
		template_values = {
			'greetings': greetings,
			'url': url,
			'url_linktext': url_linktext,
			'room':room,
			'leftComment':leftComment,
		
		}
		
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))

class GetGreetingByID(webapp.RequestHandler):
	def get(self):
		IDs=eval(self.request.get('IDs'))
		greetings=[];
		for	id in IDs:
			greetings+=[db.get( db.Key(id) )];
		
		template_values = {
			'greetings': greetings,
			'url': None,
			'url_linktext': None,
			'room': None,
			'leftComment':	0,
		
		}
		
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, template_values))

class GetID(webapp.RequestHandler):
	def get(self):
		room=self.request.get('room')
		maxComment=self.request.get('maxcm')
		if not maxComment: maxComment=8
		else:maxComment=int(maxComment)
		#greetings_query = Greeting.all().ancestor(guestbook_key(guestbook_name)).order('-date')
		
		greetings_query = db.GqlQuery("SELECT __key__ FROM Greeting Where room=:1 ORDER BY date DESC",room)
		data = greetings_query.fetch(maxComment)
		
		IDs=reversed(data);
		
		template_values = {
			'IDs': IDs
		}
		
		path = os.path.join(os.path.dirname(__file__), 'show_id.html')
		self.response.out.write(template.render(path, template_values))

class Guestbook(webapp.RequestHandler):
	def post(self):
		# We set the same parent key on the 'Greeting' to ensure each greeting is in
		# the same entity group. Queries across the single entity group will be
		# consistent. However, the write rate to a single entity group should
		# be limited to ~1/second.
		room = self.request.get('room')
		greeting = Greeting()
		
		if users.get_current_user():
			greeting.author = users.get_current_user()
		
		greeting.content = self.request.get('content')
		greeting.room = room
		greeting.put()
		
		#find reply and send email
		#		greetings_query = db.GqlQuery("SELECT * FROM Greeting Where room=:1",room)
		#		data = greetings_query.fetch(1000)
		#		#filter for author
		#		authors= [gr.author for gr in data if gr.author]
		#
		#		replyTo=res.reply.findall(greeting.content)
		#		replyTo=[str(nickname.replace("@","")) for nickname in replyTo]
		#
		#		toUsers={}
		###		text="Nicknames:\n"
		#		for user in authors:
		###			text+=user.nickname()+"\n"
		#			if user.nickname() in replyTo or user.email() in replyTo:
		#				toUsers.setdefault(user.user_id(),user)
		###		text+="Author:"+str(authors)+"\n"
		###		text+="\nReply to:"+str(replyTo)
		#		for id in toUsers:
		###			text+="\nSend email to "+toUsers[id].email()
		#			message = mail.EmailMessage()
		#			message.sender = greeting.author.nickname()+" <reply-notifier@ict-chat.appspotmail.com>"
		#			message.subject = "You have reply from "+greeting.author.nickname()+" using ict-chat.appspot.com service"
		#			message.to = toUsers[id].email()
		#			message.body = """%s reply to you at http://ict-chat.appspot.com/?room=%s
		#Content:%s
		#
		#P/s: Do not reply to this email
		#				  """%(greeting.author.nickname(),room,greeting.content)
		#			message.send()
		
		##ict-chat.appspot.com-noreply <"
		
		#self.response.out.write(text)
		self.redirect('/?' + urllib.urlencode({'room': room }))


def main():
	application = webapp.WSGIApplication([
										  ('/', MainPage),
										  ('/sign', Guestbook),
										  ('/id', GetID),
										  ('/show', GetGreetingByID),
										  ], debug=True)
	
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
