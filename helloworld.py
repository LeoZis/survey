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

class MainPage(webapp2.RequestHandler):
  def get(self):
	user = users.get_current_user()
	if not user:
		self.redirect(users.create_login_url(self.request.uri))
	else:
		self.response.out.write('<html><body>')

		surveys = db.GqlQuery("SELECT * "
								"FROM Survey "
							  )

		for survey in surveys:
			self.response.out.write(
				'<b>%s</b> Survey:' % survey.author.nickname())
			self.response.out.write('<blockquote>%s</blockquote>' %
								  cgi.escape(survey.name))

		self.response.out.write("""
			  <form action="/survey" method="post">
				<div><input type = "text" name="name"></input></div>
				<div><input type="submit" value="Create Survey"></div>
			  </form>
			</body>
		  </html>""")


class SurveyCreate(webapp2.RequestHandler):
  def post(self):
    survey = Survey()

    if users.get_current_user():
      survey.author = users.get_current_user()

    survey.name = self.request.get('name')
    survey.put()
    self.response.out.write('congratulations, your survey has been made.')

app = webapp2.WSGIApplication([('/', MainPage),
							 ('/survey', SurveyCreate)],
                              debug=True)