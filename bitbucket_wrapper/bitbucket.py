from collections import defaultdict, OrderedDict
import requests
import grequests

from requests_futures.sessions import FuturesSession

import re

session = FuturesSession()
commit_result = defaultdict(list)
global_users = ''

class bitbucket_api():
	PAGE_LEN = 100
	BASE_URL = 'https://bitbucket.org/api/2.0/%s/%s'
	USERS = ''
	ACCESS_TOKEN = ''
	ordered_commit_result = OrderedDict()

	def __init__(self, access_token, bitbucket_user_id):
		self.ACCESS_TOKEN = access_token
		self.USERS = bitbucket_user_id

	def __repr__(self):
		return self.ordered_commit_result

	def get_url(self, url):
	    return url + '?access_token=' + self.ACCESS_TOKEN + '&pagelen=' + str(self.PAGE_LEN)

	def get_user_info(self):
		r = requests.get(self.BASE_URL % ('users', self.USERS) + '?access_token=' + self.ACCESS_TOKEN)
		user_info = r.json()
		global global_users
		global_users = user_info['username']
		self.USERS = user_info['username']

		return user_info

	def get_repositories(self):
		res = self.get_user_info()
		repo_json = []
		_repo_link = self.get_url(res['links']['repositories']['href'])

		while(True):
			_repo = requests.get(_repo_link)
			_repo_json = _repo.json()
			repo_json.append(_repo_json)
			try:
				if _repo_json['next']:
					_repo_link = _repo_json['next']
			except KeyError:
				break

		return repo_json

	def get_commit(self):
		_repo_slug = self.get_repositories()
		# commit_result = defaultdict(list)
		req_url = []

		for repo in _repo_slug:
			for commit_links in repo['values']:
				_commit_link = self.get_url(commit_links['links']['commits']['href'])
				req_url.append(_commit_link)

		rs = (grequests.get(u, hooks=dict(response=bitbucket_api.get_slug_commit)) for u in req_url)
		a = grequests.map(rs)

		self.ordered_commit_result = OrderedDict(sorted(commit_result.items()))
		return self.ordered_commit_result

	def get_commit_count(self):
		cnt = 0
		for commit in self.ordered_commit_result:
			cnt += len(commit)

		return cnt

	@staticmethod
	def get_slug_commit(res, *args, **kwargs):
		_commit_link = res.url
		while(True):
			_commits = requests.get(_commit_link)
			_commits_json = _commits.json()
			for _commit in _commits_json['values']:
				try:
					print global_users
					# print _commit['author']['user']['username'].encode('utf8') == str(global_users)
					if _commit['author']['user']['username'].encode('utf8') == global_users:
						date = re.findall(r'(.*?)T', _commit['date'])[0]
						commit_result[date].append(_commit)
				except KeyError, NameError:
					pass
			try:
				if _commits_json['next']:
					_commit_link = _commits_json['next']
			except KeyError:
				break


