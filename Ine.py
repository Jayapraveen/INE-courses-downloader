"""
Version: 1.0.0 Stable Nightly (alpha release)
Author: Jayapraveen AR
Credits: Donald Martinez
Program Aim: To download courses from INE website for personal and educational use
Location : India
Date : 23/05/2020
To Do:
1. Make resumable downloader in Site rip if error occurs
2. Fix issue exiting program while refetching tokens
3. Optimize for efficiency and memory footprint
4. Make program multithreaded
5. Compile the endpoints and data handling logic to prevent abuse and protect the authenticity of this script
6. Try to implement login using credentials
7. Try to bypass google v2 verification
8. Move all configurations to seperate configuration file
9. Reduce input faults if any
10. Make more autonomous with cli invocation and args parsing
Bug reporting: Please report them if any in issues tab
"""
import requests
import json
import os
from time import sleep
from tqdm import tqdm

#script location
script_path = os.getcwd()
token_path = script_path + '/ine_tokens.txt'
#Download location
custom = False
if(custom):
    save_path = ""
else:
    save_path = "./"
#token
with open(token_path,'r') as fp:
    fp = json.loads(fp.read())
access_token = fp["access_token"]
refresh_token = fp["refresh_token"]
#access_token = "eyJraWQiOiJsNlRId2RYZXdRTmh5NlJ2QTB2YnZnT0NPeWVaUkxvazM2b205dnU1Q0hFPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3YjYzZmRhOS05ZGVjLTQ5NGQtOTQzNS1mYzYzOTk3NjMzY2EiLCJldmVudF9pZCI6ImJlMjhlMGM5LTFkMTctNGU4Yi1hMTM2LTQzN2QyNTEyNTZkMCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE1OTAxNTEwOTUsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX2d4SWlFV2Z0QSIsImV4cCI6MTU5MDE1NDY5NSwiaWF0IjoxNTkwMTUxMDk1LCJqdGkiOiI1N2I3YjYxMS03OTM3LTQ3OGUtYWE3Ni1jOTdhNjU2MjFhMmUiLCJjbGllbnRfaWQiOiIyNHZxdWdmNzFlbW9kdjI5cDVzOXY2am9oOSIsInVzZXJuYW1lIjoiN2I2M2ZkYTktOWRlYy00OTRkLTk0MzUtZmM2Mzk5NzYzM2NhIn0.WaSWwamJ8WIEbtwAQtFd5U9KfkNlqEA7frA3S_xXBreeYr6S81ShDWMxDNMAEstDXKmrPf7Q0zm2uDmM7JZVPaOE_0V47hLHPnGg4gKCnNdmpLB6dqoXOhFCylAWVVz53-NgVKvWYbxnvtYw_BIzhA3bmP_ELNolwZ35Di5c8R-4DSUQku5OQEQuCjum2rKXk8PGRoxXRheXrADt3IN3N8cWEtf7pwMEgLHVOnNKSGYcSWLg_mOaP9a6c5Yv5IeWc4sJTGzpiDSr26-YL0ryIQMzYYiuZ_2oUVBMTL9EYVI5WpdHec_opV9OvkRH8A9ph4REhj4h-TBlgTqhINbEtw"
#refresh_token = "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiUlNBLU9BRVAifQ.DlSEFMMXwDY16M_5wl1Zg5N8X7NxsFP2sFjgtg0_G3OpcNAMjAeNlsFJLucQ40nKiX9lpwTET7jbxX1oIWs76agTfIp5CAZyMG_bsdKS7SPYjPoNyPaezAdtyyWHT-rB8UIeKfMHBEWmz6oM0RgHjRjgau05ibhkQUVsl4BZ6CDYCxv-wUq3zyPxWSAS9tDaIeMV7fkfBwuC7BQNbYQV7KyHn0ZYheNdzpo6zFLu3HppefWRDgeZqiJtVkx-bGbkLH1kfwVn2oMROZ3zYh2NFhNEqQjW0sY-hwM17R9agEkHAWZN60VnaHDypmAX1_ldK3CiZcgl9tLeA7uwnH9_jQ.dODnqpCcG5FgHoDy.5u37f_ctE3Mz0TRhjoBbJsX6q-B_3GbnWDShmcCYMLpRexuF3C5jSPJ4uXtin06sbwnNbHWhfNgPfwYuwK5JXS02tIOYns3tTXITpwLSHy3xNK7pls0DGN2jH8-KsbzkyrssF8calvLue3_hlOVgqsvwWDDAUpt5g0DQLagwOPUbdw0Jmo1srTi0MyJtYoZCSTQcOVbK40MA_JmoWgw_V5tIto1xL6rP7SMJA0KxhvCnfbmMi_IrNO5MzTYKJZMVgtLjlIV585NjWfjPtfIu6f_TxOpA5ZTQsr90-6Nr51mJyEqcfeCIEumw96_nwnXCX0Qx90m1SSuLcUo19jRpDhAq3nQzLIIMWWJv3sKiLGvpC3A4UlfIB9Jl0I4ne9GsCy-xT1IWGfqg0ESxrWL6QGs_3-eill9n92SviG2mso0XR7n7iKk4vsWS9tnlMtZUu9x7xNVe59z5p2TBfjyOvQV2tx1jSUFxcKj_lZr6Io3_8sm2FsjdgUEVc3sW3x6UAH4Mxp-jy9D1DSr5XHdN2Mk2lQky071GVsFdkKU-rS_TMCY0zl-J-QJzbhoIdPmqnWvRU46vVWFma0VaR8BTigGvtMQY_i60EAdqZfhVWYOUGQVsXT2tQMjfaEuieg-pdhJGOjbCtf1dFJZ7vLJRkGG1WbltepKR5X7JYkk6CdiCBuCADAqYhMln3PJKdKd20-Y-ofBCvCAPt1i6bGMz88Ci5_xEYVyp7VzH5C3Z6JhpoTMBIrvl13Hj9NqDisrUOZC_oHEBjPdYXPoZTr7UMoV61eBxkmd9t2Sz2_fRVVIqBYd1lsTXqrDGBS-ObTECFHuuQYY3igiqgA8DPi921OmzzyjXUtqt4TQcKrmLDECVYvCkC3WOPqXnx3kgSPX-85YkgKwj-IMJocwNj3buh8PWdvf_e5VPIlY3ygusBdJRCuwNSVouD2cYHA42EpoXTaulwZV1dsZjVM7vq64bHAJbCP0sxYifKe4pfgQqqLdNt1Jq2jqyLHi3vvtqb9fckLYfLwSnH4UmOhagbaKWjwre2aVWSOAQZs4ag7oQu9tzkriOjycepVOnCWKrJFdG1uBtOy-eYLOXUYP3AuwIF4JcEk3on4I571i1ThjFZHedyrGS1mvWysd9JiU_PHLJn51Yf8iY7YB-oEaJnqtILOBLiE9l39PPmTPgjWNxSYZjSX7naHBJNOVu1Pk7Q65X_zWzCSD9fV5qpVx7AchBkSh0T30ZSmjQ2v-PhnaSPdodo6usSopRoN6El2N-ws9YnE2Z5_xxw0k15QR6dFOjwUxCMuzi80PDS_Ky9NWCyKqiQnyeoQZrcN9uCw.si4g-OBee6nJNyNyuX_BJQ"
access_token = "Bearer "+ access_token
#headers
accept = "application/json, text/plain, */*"
x_requested_with = "com.my.ine"
sec_fetch_site = "cross-site"
sec_fetch_mode = "cors"
sec_fetch_dest = "empty"
content_type = "application/json;charset=UTF-8"
user_agent = "Mozilla/5.0 (Linux; Android 6.0;PIXEL XL Build/INE) Mobile Safari/537.29"
referer = "http://localhost"
accept_encodings = "gzip, deflate, br"
#endpoints
all_courses_url = "https://content-api.rmotr.com/api/v1/courses?active=true&page_size=none&ordering=-created"
video_url = "https://video.rmotr.com/api/v1/videos/{}/media"
subscription_url = "https://subscriptions.ine.com/subscriptions/subscriptions?embed=passes"
refresh_token_url = "https://uaa.ine.com/uaa/auth/refresh-token"
auth_check_url = "https://uaa.ine.com/uaa/auth/state/status"

def auth_check():
    host = "uaa.ine.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    auth_valid = requests.get(auth_check_url,headers = header)
    user = json.loads(auth_valid.text)
    #print(email)
    if(auth_valid.status_code == 200):
        if(user["data"]["email"]):
            email = user["data"]["email"]
            fname = user["data"]["profile"]["data"]["first_name"]
            lname = user["data"]["profile"]["data"]["last_name"]
            print("Logged in to INE as {}\n".format(email))
            print("Your name is {} {}\n".format(fname,lname))

    elif(auth_valid.status_code == 401):
        print("Access token expired!\nTrying to refresh..")
        access_token_refetch()
        auth_check()

def access_token_refetch():
    global access_token
    global refresh_token
    host = "uaa.ine.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    refresh_data = json.dumps({"refresh_token":refresh_token})
    out = requests.post(refresh_token_url, data = refresh_data , headers = header)
    if(out.status_code == 200):
        #print(out.text)
        out = json.loads(out.text)
        access_token = out["data"]["tokens"]["data"]["Bearer"]
        #print(refresh_token)
        refresh_token = out["data"]["tokens"]["data"]["Refresh"]
        #print(refresh_token)
        with open(token_path,'w') as fp:
            tokens = {"access_token": access_token,"refresh_token": refresh_token}
            fp.write(json.dumps(tokens))
        print("Got new tokens")
    elif(out.status_code == 401):
        #refresh_token invalid
        print("Failure, Get new tokens manually!\n")
        exit()

def pass_validator():
    host = "subscriptions.ine.com"
    header = {"Host": host,"Origin": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Referer": referer}
    passes = requests.get(subscription_url,headers = header)
    if(passes.status_code == 200):
        #print(passes.text)
        passes = json.loads(passes.text)
        if(len(passes["data"]) != 0):
            passes = passes["data"][0]["passes"]["data"]
            pass_avail = []
            #print("Subscriptions passes in your account are:")
            for i in passes:
                pass_avail.append("INE " + i["name"])
                #print("INE " + i["name"])
            return pass_avail
        else:
            print("No subscriptions found in your account! Program cannot proceed further\n")
            exit()
    elif(passes.status_code == 500):
        print("Ine Subscriptions Server error\n")
    return passes

def sanitize(course_name):
    if(course_name.split(':')[0] == "Video"):
        course_name = course_name.split('/')[-1]
        return course_name
    else:
        return course_name + '.mp4'

#Video metadata getter
def get_meta(uuid,quality):
    host = "video.rmotr.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    out = requests.get(video_url.format(uuid),headers = header)
    if out.status_code == 200:
        out = json.loads(out.text)
        #print(out)
        name = sanitize(out["title"])
        #print(name)
        for i in out["playlist"][0]["sources"]:
            try:
                if(i["height"] == quality):
                    video = i["file"]
            except:
                continue
        subtitle = out["playlist"][0]["tracks"][0]["file"]
        out = []
        out.append(name)
        out.append(video)
        out.append(subtitle)
        return out
    elif(out.status_code == 403):
        print("No access to video metadata;\nAccess Pass check failed to identify")
        exit()
        #print("\nToken error in video meta getter\n")
        #print("Trying to update tokens\n")
        #access_token_refetch()
        #get_meta(uuid,quality)


def coursemeta_fetcher():
    all_courses = requests.get(all_courses_url)
    course_handler = open('ine_courses.txt','w')
    course_handler.write(all_courses.text)
    course_handler.close()

def total_courses():
    course_handler = open('ine_courses.txt','r')
    all_courses = json.loads(course_handler.readline())
    course_handler.close()
    length = len(all_courses)
    count = 0
    for i in all_courses:
        print("{}. {}".format(count,i["name"]))
        count = count + 1
    print ("Total {} courses\n".format(length))
    return all_courses

def download_video(url,filename):
    video = requests.get(url, stream=True)
    with open(filename, 'wb') as video_file:
        for chunk in video.iter_content(chunk_size=1024):
            if chunk:
                video_file.write(chunk)

def downloader(course,quality):
    course_name = course["name"]
    course_file = course["files"]
    if(len(course['content'][0]['content']) == 1):
        course_meta = course['content']
        #print(course_meta)
        cont_loc = 1
    else:
        course_meta = course['content'][0]['content']
        #print(course_meta)
        cont_loc = 2
    os.chdir(save_path)
    if not os.path.exists(course_name):
        os.makedirs(course_name)
    os.chdir(course_name)
    pbar = tqdm(course_file)
    for i in pbar:
        command = "curl '{}' --output '{}' -s".format(i["url"],i["name"])
        os.popen(command).read()
        pbar.set_description("Downloading course file: %s" % i["name"])
        pbar.update()
    pbar = tqdm(course_meta)
    for i in pbar:
        #print(i)
        subtopic_name = i["name"]
        if(cont_loc == 1):
            course_meta = i["content"][0]["content"]
        else:
            course_meta = i["content"]
        if not os.path.exists(subtopic_name):
            os.makedirs(subtopic_name)
        os.chdir(subtopic_name)
        for j in course_meta:
            if(j["content_type"] == "video"):
                out = get_meta(j["uuid"],quality)
                #print(out[0])
                #print(out[1])
                #print(out[2])
                download_video(out[1],out[0])
                command = "curl '{}' --output {} -s".format(
                out[2],
                out[0] + '.vtt'
                )
                os.popen(command).read()
        os.chdir('../')
        pbar.set_description("Downloading: %s" % course_name)
        pbar.update()
    os.chdir('../')
    print("Selected course has been downloaded\n")


if __name__ == '__main__':
    os.system('clear')
    print("INE Courses Downloader\n")
    if(len(access_token) == 0):
        print("Please refer to readme.md in github and set the access_token")
        exit()
    if(len(access_token) != 1009):
        #print(len(access_token))
        print("Access token entered is faulty. Check for and correct errors!")
        exit()
    if(len(refresh_token) == 0):
        print("Please refer to readme.md in github and set the refresh_token")
        exit()
    if(len(refresh_token) != 1784):
        print(len(refresh_token))
        print("Refresh token entered is faulty. Check and correct errors!")
        exit()
    print("Warning! Until the script completes execution do not access INE website or mobile app\n as it might invalidate the session token!\n")
    auth_check()
    access_pass = pass_validator()
    method = int(input("Choose Method Of Operation:\n1.Site Rip\n2.Select Individual Course\n"))
    if (os.path.isfile('ine_courses.txt')):
        all_courses = total_courses()
    else:
        coursemeta_fetcher()
        all_courses = total_courses()
    quality = int(input("Choose Preferred Video Quality\n1.1080p\n2.720p\n"))
    if(quality == 2):
        quality = 720
    else:
        quality = 1080
    if(method == 1):
        cons = input("Warning! This is a high compute and throughput functionality and needs\nlots and lots of compute time and storage space \nEnter \"I agree\" to acknowledge and proceed!\n")
        if(cons != "I agree"):
            print("User did not accept! Program exiting")
            exit()
        print("\nInitialzing for Site dump\n")
        #bam method courses scheduler logic
        total_course = len(all_courses)
        course_batch = 6
        for i in range(total_course):
            print("Course NO:",i)
            if(i % course_batch == 0 and i != 0):
                print('Course batch complete \nWaiting 1 minute before resuming')
                sleep(60)
                access_token_refetch()
            course = all_courses[i]
            #print(course)
            if(course["access"]["related_passes"][0]["name"] in access_pass):
                downloader(course,quality)
    else:
        choice = int(input("Choose Method Of Selecting Course\n1.Enter url\n2.Choose from the above listed course\n"))
        if(choice == 1):
            url = input("Paste the url\n")
            try:
                for i in all_courses:
                    if(i["url"] == url):
                        choice = i
            except Exception as e:
                print('URL not found, Choose other method for selecting course\n', e.args)
                exit()
            course = choice
            #if(course["access"]["related_passes"][0]["name"] in access_pass):
            downloader(course,quality)

        elif(choice == 2):
            choice = int(input("Please enter the number corresponding to the course you would like to download\n"))
            course = all_courses[choice]
            #print(course)
            #if(course["access"]["related_passes"][0]["name"] in access_pass):
            downloader(course,quality)
        else:
            exit("Invalid choice!\n")