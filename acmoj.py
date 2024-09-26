#!/usr/bin/env python3
import requests
import re
import os
from getpass import getpass
from datetime import datetime

cache_path = os.path.expanduser("~/.cache/acmoj/")
config_path = os.path.expanduser("~/.config/acmoj/")
author_name = os.getenv("ACMOJ_AUTHOR") or "You (your_email@sjtu.edu.cn)"
max_track_seconds = 60 * 2
track_interval_seconds = 1

class source_file_handler:
	file_info = '''// -*- coding: utf-8 -*-
// Date             : {date}
// Author           : {author}
// Problem ID       : {problem_id}
// Algorithm Tag    : {algorithm_tag}
'''
# problem_id may contain a suffix like "-bf", "-std", " WA", " TLE", etc
# the suffix can be split by a space or a dash
# the suffix will be ignored when submitting
	template_path = config_path + "template.cpp"
	def __init__(self):
		self.source = ""
		self.date = None
		self.author = author_name
		self.problem_id = None
		self.algorithm_tag = None

	def parse(self, source : str):
		self.source = ""
		comment_lines = []
		comment_end = False
		for line in source.split("\n"):
			if not comment_end and line.startswith("//"):
				comment_lines.append(line)
			else:
				comment_end = True
				self.source += line + "\n"
		self.source = self.source.strip()
		self.date = self.author = self.problem_id = self.algorithm_tag = None
		for line in comment_lines:
			if line.startswith("// Date"):
				self.date = line.split(": ")[1].strip()
			elif line.startswith("// Author"):
				self.author = line.split(":")[1].strip()
			elif line.startswith("// Problem ID"):
				self.problem_id = line.split(":")[1].strip()
			elif line.startswith("// Algorithm Tag"):
				self.algorithm_tag = line.split(":")[1].strip()
		return self

	def generate(self, problem_id, algorithm_tag="", source=""):
		if source:
			self.parse(source)
			source = self.source
		else:
			try:
				with open(self.template_path, "r") as f:
					source = f.read()
			except FileNotFoundError:
				raise Exception("Template file not found!")
		return self.file_info.format(
			problem_id=problem_id,
			date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			author=self.author,
			algorithm_tag=algorithm_tag,
		) + source

class SubmissionStatus:
	def __init__(self):
		self.possible_columns = {
			"submission_id": "编号",
			"username": "昵称",
			"problem": "题目",
			"status": '评测状态',
			"score": '分数',
			"time": "运行时间",
			"memory": "内存",
			"language": "语言",
			"submit_time": "提交时间",
		}
		self.status_dict = {}
		self.submission_id = None
		self.username = None
		self.problem = None
		self.status = None
		self.score = None
		self.time = None
		self.memory = None
		self.language = None
		self.submit_time = None
		self.done = False
		self.details = []

	def parse(self, html):
		# print("html", html)
		status_table = re.search(r'<table class="table table-striped table-bordered table-hover status-list">.*?</table>', html, re.DOTALL).group()
		# Use regex to match content within <th> tags, including nested tags
		found_columns = re.findall(r'<th[^>]*>(.*?)</th>', html, re.DOTALL)
		# Remove any HTML tags within the matched content
		found_columns = [re.sub(r'<[^>]+>', '', col).strip().rstrip('?') for col in found_columns]
		columns = {}
		for column_name, column_title in self.possible_columns.items():
			if column_title in found_columns:
				columns[column_name] = found_columns.index(column_title)
			else:
				columns[column_name] = None
		# found_status = re.findall(r'<td>(.*?)</td>', status_table, re.DOTALL)
		# Use regex to match content within <td> tags, including nested tags
		found_status = re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL)
		# Remove any HTML tags within the matched content
		found_status = [re.sub(r'<[^>]+>', '', col).strip() for col in found_status]
		# print("found_status", found_status)
		for column_name, column_index in columns.items():
			if column_index is not None:
				self.status_dict[column_name] = found_status[column_index]
			else:
				self.status_dict[column_name] = None
		if self.status_dict["submission_id"] is not None:
			self.status_dict["submission_id"] = int(self.status_dict["submission_id"])
		if self.status_dict["time"] is not None:
			self.status_dict["time"] = re.search(r'(\d+) ms', self.status_dict["time"], re.DOTALL).group(1)
			self.status_dict["time"] = int(self.status_dict["time"])
		if self.status_dict["memory"] is not None:
			self.status_dict["memory"] = re.search(r'(\d+) KiB', self.status_dict["memory"], re.DOTALL).group(1)
			self.status_dict["memory"] = int(self.status_dict["memory"])

		self.submission_id = self.status_dict["submission_id"]
		self.username = self.status_dict["username"]
		self.problem = self.status_dict["problem"]
		self.status = self.status_dict["status"]
		self.score = self.status_dict["score"]
		self.time = self.status_dict["time"] or self.time
		self.memory = self.status_dict["memory"] or self.memory
		self.language = self.status_dict["language"]
		self.submit_time = self.status_dict["submit_time"]
		self.done = self.status is not None \
			and self.status not in ("Pending", "Compiling", "Judging")

		details_div = re.search(r'<div class="m-auto">.*?</div>', html, re.DOTALL).group()
		details = re.findall(r'<a.*?>(.*?)</a>', details_div, re.DOTALL)
		details = [detail.strip() for detail in details]
		self.details = details or self.details

		if self.status is None:
			raise Exception("Submission status not found!")
		return self

	def pretty_print(self):
		score = str(self.score) if self.score is not None else ""
		res = f"{self.status:<{10}} {score:<{3}} {self.problem}, "
		res += f"{self.time}ms, {self.memory}KiB, " if self.time is not None and self.memory is not None else ""
		res += f"{self.language}, {self.submit_time} Details: {', '.join(self.details)}"
		return res

class ACMOJ_helper:
	root_url = "https://acm.sjtu.edu.cn/OnlineJudge/"
	login_cookie_path = cache_path + "login_cookie.txt"
	last_submission_path = cache_path + "last_submission_id.txt"
	headers = {
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
		'X-Acmoj-Is-Csrf' : 'no'
	}

	def __init__(self):
		self.session = requests.Session()
		self.session.headers.update(self.headers)
		self.login_cookie = None

	def get_new_login_cookie(self, username, password):
		login_url = self.root_url + "login"
		login_data = {
			"username": username,
			"password": password,
		}
		session = requests.Session()
		session.headers.update(self.headers)
		session.post(login_url, data=login_data)
		login_cookie = session.cookies.get("acmoj-session")
		# make sure that login_cookie is not None, and is a uuid
		if login_cookie is None or re.match(r"[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", login_cookie) is None:
			raise Exception("Login failed! Got cookie: " + str(login_cookie))
		return login_cookie

	def validate_login_cookie(self, login_cookie):
		if login_cookie is None or re.match(r"[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", login_cookie) is None:
			return False
		validate_url = self.root_url + "login"
		# if the returned page contains "登出", then the cookie is valid
		return "登出" in self.session.get(validate_url, cookies={"acmoj-session": login_cookie}).text

	def store_login_cookie(self, login_cookie):
		with open(self.login_cookie_path, "w") as f:
			f.write(login_cookie)

	def login(self, username = "", log=True):
		login_cookie = self.login_cookie
		if login_cookie is None:
			with open(self.login_cookie_path, "r") as f:
				login_cookie = f.read()
		if not self.validate_login_cookie(login_cookie):
			if log:
				print("Login cookie is invalid. Getting a new one...")
			else:
				raise Exception("Login cookie is invalid!")
			username = username or input("Username: ")
			password = getpass("Password: ")
			login_cookie = self.get_new_login_cookie(username, password)
			if log:
				print("Got new login cookie:", login_cookie)
			if not self.validate_login_cookie(login_cookie):
				raise Exception("Login cookie is still invalid!")
			self.store_login_cookie(login_cookie)
		self.login_cookie = login_cookie
		self.session.cookies.update({"acmoj-session": login_cookie})
		if log:
			print("Login successful.")

	def submit(self, source:str, problem_id, language="cpp"):
		submit_url = self.root_url + f"problem/{problem_id}/submit"
		submit_data = {
			"language": language,
			"code": source,
			"problem_id": problem_id,
		}
		response = self.session.post(submit_url, data=submit_data)
		match = re.search(r"code/(\d+)/", response.url)
		if not match:
			raise Exception("Submission failed! Got response:\n" + response.text)
		submission_id = match.group(1)
		with open(self.last_submission_path, "w") as f:
			f.write(submission_id)
		return submission_id

	def get_submission_url(self, submission_id):
		return self.root_url + "code/" + str(submission_id)

	def get_submission_status(self, submission_id, status=None):
		submission_url = self.get_submission_url(submission_id)
		submission_response = self.session.get(submission_url)
		if submission_response.status_code != 200:
			raise Exception("Submission not found! Got status code: " + str(submission_response.status_code))
		submission_page = submission_response.text
		status = status or SubmissionStatus()
		status.parse(submission_page)
		return status

	def abort_judging(self, submission_id):
		abort_url = self.root_url + "code/" + str(submission_id) + "/abort"
		response = self.session.post(abort_url)
		if response.status_code != 200:
			raise Exception("Abort failed! Got status code: " + str(response.status_code))

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(dest="subcommand", required=True)
	login_parser = subparsers.add_parser("login", description="Login to ACMOJ.")
	login_parser.add_argument("-u", "--username")

	submit_parser = subparsers.add_parser("submit", description="Submit to ACMOJ.")
	submit_parser.add_argument("source_path")
	submit_parser.add_argument("-p", "--problem", type=int)
	submit_parser.add_argument("-t", "--track", action="store_true", help="Track the submission status.")
	submit_parser.add_argument("-l", "--language", type=str, default="cpp", help="Specify the language of the source code.")

	status_parser = subparsers.add_parser("status", description="Get the status of a submission.")
	status_parser.add_argument("submission_id", nargs='?', type=int)

	newfile_parser = subparsers.add_parser("new", description="Create a new source file.")
	newfile_parser.add_argument("problem_id", type=str) # problem_id may contain a suffix
	newfile_parser.add_argument("source_path", nargs="?", type=str, default="", help="Use the specified source code instead of the template.")
	newfile_parser.add_argument("-a", "--algorithm-tag", dest="tag", type=str, default="")

	helper = ACMOJ_helper()
	args = parser.parse_args()

	if args.subcommand == "login":
		username = args.username
		helper.login(username)
	elif args.subcommand == "submit":
		helper.login(log=False)
		try:
			with open(args.source_path, "r") as f:
				source = f.read()
		except FileNotFoundError:
			print("File not found:", args.source_path)
			exit(1)
		problem_id = args.problem
		parser = source_file_handler().parse(source)
		if problem_id is None:
			problem_id = parser.problem_id
			if problem_id is None:
				print("Problem ID not specified!")
				exit(1)
			problem_id = problem_id.split("-")[0]
			problem_id = problem_id.split(" ")[0]
			print("Problem ID not specified. Using the problem ID in the source file:", problem_id)
		# make sure that the problem ID is a number
		if re.match(r"\d+", str(problem_id)) is None:
			print("Invalid problem ID:", problem_id)
			exit(1)
		language = args.language
		submission_id = helper.submit(source, problem_id, language=language)
		print("Submission successful. Submission ID:", submission_id)
		print("See the submission status at", helper.get_submission_url(submission_id))
		if args.track:
			status = SubmissionStatus()
			max_length = 0
			try:
				import time
				start_time = time.time()
				while True:
					status = helper.get_submission_status(submission_id, status)
					output = " " + status.pretty_print()
					max_length = max(max_length, len(output))
					print(output + " " * (max_length - len(output)), end="\r")
					if status.done:
						print(output + " " * (max_length - len(output)), end="\r\n")
						break
					time.sleep(track_interval_seconds)
					if time.time() - start_time > max_track_seconds:
						print("\nTrack time limit exceeded. Stop tracking.")
						break
			except KeyboardInterrupt:
				helper.abort_judging(submission_id)
				print("\nJudging aborted.")
	elif args.subcommand == "status":
		helper.login(log=False)
		submission_id = args.submission_id
		if submission_id is None:
			with open(helper.last_submission_path, "r") as f:
				submission_id = int(f.read())
			print("Submission ID not specified. Using the last submission ID:", submission_id)
		try:
			status = helper.get_submission_status(submission_id)
		except Exception as e:
			print("Error:", e)
			exit(1)
		print(status.pretty_print())
		print("See the full submission status at", helper.get_submission_url(submission_id))
	elif args.subcommand == "new":
		problem_id = args.problem_id
		source_path = args.source_path
		algorithm_tag = args.tag
		if os.path.exists(problem_id + ".cpp"):
			print("File already exists:", problem_id + ".cpp")
			exit(1)
		if source_path:
			try:
				with open(source_path, "r") as f:
					source = f.read()
			except FileNotFoundError:
				print("File not found:", source_path)
				exit(1)
		else:
			source = ""
			print("Source code not specified. Using the template.")
		try:
			code = source_file_handler().generate(problem_id, algorithm_tag, source)
		except Exception as e:
			print("Error:", e)
			exit(1)
		try:
			with open(problem_id + ".cpp", "w") as f:
				f.write(code)
			print("New file created:", problem_id + ".cpp")
			os.system("code " + problem_id + ".cpp")
		except Exception as e:
			print("Error:", e)
			exit(1)