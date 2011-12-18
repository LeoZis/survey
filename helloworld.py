import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db
from google.appengine.api import users


class Survey(db.Model):
	"""Models an individual Survey entry with an author and name"""
	author = db.UserProperty()
	name = db.StringProperty(multiline=True)
  
class Question(db.Model):
    survey = db.ReferenceProperty(Survey, collection_name='questions')
    question = db.StringProperty()
	
class Choice(db.Model):
	question = db.ReferenceProperty(Question, collection_name='choices')
	choice = db.StringProperty()
	votes = db.IntegerProperty()

class MainPage(webapp2.RequestHandler):
  def get(self):
	user = users.get_current_user()
	if not user:
		self.redirect(users.create_login_url(self.request.uri))
	else:
		self.response.headers['Content-Type'] = 'text/html'
		self.response.out.write('<html><body>')
		self.response.out.write('<p>Welcome, %s! You can <a href="%s">Log Out</a>.</p>'
			% (user.nickname(), users.create_logout_url(self.request.path)))
		surveys = db.GqlQuery("SELECT * "
								"FROM Survey "
							  )

		for survey in surveys:
			self.response.out.write(
				'<b>%s</b> Survey:' % survey.author.nickname())
			self.response.out.write(' %s <br />' %
								  cgi.escape(survey.name))
		
		self.response.out.write('<hr>')
		self.response.out.write("""
			  <form action="/survey" method="get">
				<div><input type = "text" name="name"></input></div>
				<div><input type="submit" value="Create Survey"></div>
			  </form>
			</body>
		  </html>""")


class SurveyCreateOrEdit(webapp2.RequestHandler):
	def get(self):		
		user = users.get_current_user()	
		if user:
			name = cgi.escape(self.request.get('name'))
			survCount = Survey.all().filter('name = ', name).count()
			#if this survey does not exist yet, we will create it and ask user to fill in a question
			if not survCount:
				survey = Survey()
				survey.author = user
				survey.name = name
				survey.put()
				self.response.out.write("""<h3>You will now be creating a question for the %s survey. Fill in the question, and how many choices it will have.</h3>
					<form action="/question" method="post">
						<div>Question: <input type = "text" size = "200" name="question"></input></div><br />
						<div># of choices: <input type = "text" maxlength="2" size="2" name="choiceNum"></input></div><br />
						<input type = "hidden" name="survName" value="%s"></input>
						<div><input type="submit" value="Fill in choices"></div>
					</form>""" % (cgi.escape(survey.name),cgi.escape(survey.name)))
			#if survey DOES exist, then we will retrieve it and ask user to add a question to it
			else:
				survey = Survey.all().filter('name = ', name).get()
				surveyAuth = survey.author
				#you are only allowed to edit your own survey
				if surveyAuth == user:
					self.response.out.write(""" <h3>You have entered an existing survey (%s). To add a question to it, fill in the question and how many choices it will have. </h3> Or <a href="%s">Go Back</a><br />""" % (survey.name ,self.request.path))
					self.response.out.write("""
						<br />
						<form action="/question" method="post">
							<div>Question: <input type = "text" size = "200" name="question"></input></div><br />
							<div># of choices: <input type = "text" maxlength="2" size="2" name="choiceNum"></input></div><br />
							<input type = "hidden" name="survName" value="%s"></input>
							<div><input type="submit" value="Fill in choices"></div>
						</form>""" % cgi.escape(survey.name))
				else:
					self.response.out.write(""" <h3>You are not allowed to edit another persons survey. </h3> <a href="%s">Go Back</a>""" % self.request.host_url)
		else:
			self.redirect(users.create_login_url(self.request.uri))

class QuestionCreate(webapp2.RequestHandler):
	def post(self):
		questionStr = cgi.escape(self.request.get('question'))
		choiceNum = cgi.escape(self.request.get('choiceNum'))
		survName = cgi.escape(self.request.get('survName'))
		
		if not choiceNum.isdigit():
			self.response.out.write("""Failed adding question. Please make sure fields are correct. <a href="%s">Go Back</a>""" % self.request.host_url)
		else:
			choiceNum = int(choiceNum)
			#If the fields are correct, insert the question and create fields based on choice number
			if choiceNum > 0 and questionStr and survName:
				surv = Survey.all().filter('name = ', survName).get()
				Question(survey=surv,
				question=questionStr).put()
				
				quest = Question.all().filter('question = ', questionStr).get()
				questID = quest.key().id()
				self.response.out.write("""<br /> <form action="/choice" method="post">""")
				for i in range(0,choiceNum):
					self.response.out.write("""<div>Choice: <input type = "text" size = "100" name="choice"></input></div><br />""")
				
				self.response.out.write("""
				<input type = "hidden" name="questid" value="%s"></input>
				<input type = "hidden" name="survName" value="%s"></input>
				<div><input type="submit" value="Submit choices"></div>
				</form>""" % (questID, cgi.escape(survName)))

			else:
				self.response.out.write("""Failed adding question. Please make sure fields are correct. <a href="%s">Go Back</a>""" % self.request.host_url)
				
class ChoiceCreate(webapp2.RequestHandler):
	def post(self):
		questid = cgi.escape(self.request.get('questid'))
		self.response.out.write(questid)

app = webapp2.WSGIApplication([('/', MainPage),
							 ('/survey', SurveyCreateOrEdit),
							 ('/question', QuestionCreate),
							 ('/choice', ChoiceCreate)],
                              debug=True)