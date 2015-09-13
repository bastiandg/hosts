#!/usr/bin/env python
import os
import sys
import shutil
import re
import subprocess
import datetime

repoDirectory = "/home/bastian/hosts"
hostListUrls =    ["http://someonewhocares.org/hosts/hosts",
		"http://adaway.org/hosts.txt",
		"http://www.malwaredomainlist.com/hostslist/hosts.txt",
		"http://www.mvps.org/winhelp2002/hosts.txt",
		"http://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&startdate%5Bday%5D=&startdate%5Bmonth%5D=&star"]
gitMessage = "Hostfile change %s" % str(datetime.datetime.now())

hostListPaths = []
hostListDomains = []
for list in hostListUrls:
	m = re.match("^https?://([a-zA-Z0-9-.]*)/.*", list)
	if m == None:
		print >>sys.stderr, "hostListUrls is corrupt"
		sys.exit(2)
	hostListDomains.append(m.group(1))
	hostListPaths.append("%s/tmp/%s" % (repoDirectory, m.group(1)))

wgetReturn = 0
for hostListUrl, hostListPath in zip(hostListUrls, hostListPaths):
	wgetProcess = subprocess.Popen(["wget", "-O", hostListPath, hostListUrl])
	wgetReturn += wgetProcess.wait()

if wgetReturn != 0:
	for hostListPath in hostListPaths:
		os.remove(hostListPath)
	print >> sys.stderr, "wget failed"
	sys.exit(1)

for hostListPath, hostListDomain in zip(hostListPaths, hostListDomains):
	shutil.copyfile(hostListPath, "%s/%s/hosts" % (repoDirectory, hostListDomain))

aggregateHostList = set()
for hostListDomain in hostListDomains:
	sourceFile = open("%s/%s/hosts" % (repoDirectory, hostListDomain) , "r").read().split("\n")[:-1]
	hostList = set()

	for line in sourceFile:
		hostname = re.match("^(?!#)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*([a-zA-Z0-9-.]*).*$", line.lower())
		if hostname != None and hostname.group(2) != "" and hostname.group(2) != "localhost":
			hostList.add(hostname.group(2))
			aggregateHostList.add(hostname.group(2))

	hostListFile = open("%s/%s/hostlist" % (repoDirectory, hostListDomain), "w")
	hostFileZero = open("%s/%s/hosts.zero" % (repoDirectory, hostListDomain), "w")
	zoneFile = open("%s/%s/adserver.conf" % (repoDirectory, hostListDomain), "w")

	for host in sorted(hostList):
		hostListFile.write("%s\n" % host)
		hostFileZero.write("0.0.0.0 %s\n" % host)
		zoneFile.write("zone \"%s\" { type master; notify no; file \"/etc/bind/null.zone.file\"; };\n" % host)

	hostListFile.close()
	hostFileZero.close()
	zoneFile.close()

hostListFile = open("%s/hostlist" % repoDirectory, "w")
hostFile = open("%s/hosts" % repoDirectory, "w")
hostFileZero = open("%s/hosts.zero" % repoDirectory, "w")
zoneFile = open("%s/adserver.conf" % repoDirectory, "w")

for host in sorted(aggregateHostList):
	hostListFile.write("%s\n" % host)
	hostFile.write("127.0.0.1 %s\n" % host)
	hostFileZero.write("0.0.0.0 %s\n" % host)
	zoneFile.write("zone \"%s\" { type master; notify no; file \"/etc/bind/null.zone.file\"; };\n" % host)

hostListFile.close()
hostFile.close()
hostFileZero.close()
zoneFile.close()

os.chdir(repoDirectory)
diffProcess = subprocess.Popen(["git", "diff", "--exit-code"])
diffReturn = diffProcess.wait()
print "Git diff return: %r" % diffReturn
if diffProcess.wait() != 0:
	gitProcess = subprocess.Popen(["git", "commit", "-a", "-m", gitMessage])
	gitReturn = gitProcess.wait()
	print "Git commit return: %r" % gitReturn

for hostListPath in hostListPaths:
	os.remove(hostListPath)
