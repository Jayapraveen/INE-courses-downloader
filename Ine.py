"""
Version: 1.2.1 Stable (beta release)
Author: Jayapraveen AR
Credits: @Dexter101010
Program Aim: To download courses from INE website for personal and educational use
Location : India
Date : 25/05/2020
To Do:
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
import shutil
from time import sleep
from tqdm import tqdm

#script location
script_path = os.getcwd()
token_path = script_path + '/ine_tokens.txt'
course_completed_path = script_path + '/ine_completed_course.txt'
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
preview_url = "https://cdn.jwplayer.com/v2/media/"

def auth_check():
    host = "uaa.ine.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    auth_valid = requests.get(auth_check_url,headers = header)
    user = json.loads(auth_valid.text)
    if(auth_valid.status_code == 200):
        if(user["data"]["email"]):
            email = user["data"]["email"]
            fname = user["data"]["profile"]["data"]["first_name"]
            lname = user["data"]["profile"]["data"]["last_name"]
            print("Logged in to INE as {} {} with {}\n".format(fname,lname,email))

    elif(auth_valid.status_code == 401):
        print("Access token expired!\nTrying to refresh..")
        access_token_refetch()
        print("Waiting 5 seconds before resuming operations!\n")
        sleep(5)
        auth_check()

def access_token_refetch():
    global access_token
    global refresh_token
    host = "uaa.ine.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    refresh_data = json.dumps({"refresh_token":refresh_token})
    out = requests.post(refresh_token_url, data = refresh_data , headers = header)
    if(out.status_code == 200):
        out = json.loads(out.text)
        access_token = out["data"]["tokens"]["data"]["Bearer"]
        refresh_token = out["data"]["tokens"]["data"]["Refresh"]
        with open(token_path,'w') as fp:
            tokens = {"access_token": access_token,"refresh_token": refresh_token}
            fp.write(json.dumps(tokens))
        access_token = "Bearer "+ access_token
        print("Got new tokens")
    elif(out.status_code == 401):
        print("Failure, Get new tokens manually!\n")
        exit()

def update_downloaded(course_index):
    with open(course_completed_path,'w') as cci:
        cci.write(course_index)

def course_preview_meta_getter(preview_id,quality):
    video_preview_url = preview_url + preview_id
    video = requests.get(video_preview_url)
    video = json.loads(video.text)
    out = []
    title = video["title"] + '.mp4'
    out.append(title)
    video = video["playlist"][0]["sources"]
    for i in video:
        try:
            if(i["height"] == quality):
                video = i["file"]
                out.append(video)
        except:
            continue
    return out


def pass_validator():
    host = "subscriptions.ine.com"
    header = {"Host": host,"Origin": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Referer": referer}
    passes = requests.get(subscription_url,headers = header)
    if(passes.status_code == 200):
        passes = json.loads(passes.text)
        if(len(passes["data"]) != 0):
            passes = passes["data"][0]["passes"]["data"]
            pass_avail = []
            for i in passes:
                pass_avail.append("INE " + i["name"])
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
        name = sanitize(out["title"])
        for i in out["playlist"][0]["sources"]:
            try:
                if(i["height"] == quality):
                    video = i["file"]
            except:
                continue
        out = []
        out.append(name)
        out.append(video)
        return out
    elif(out.status_code == 403):
        print("No access to video metadata;\nAccess Pass check failed to identify or error after token")
        exit()


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
    video_length = int(video.headers.get('content-length'))
    if video.status_code is 200:
        with open(filename, 'wb') as video_file:
            shutil.copyfileobj(video.raw, video_file)
        if os.path.getsize(filename) >= video_length:
            pass
        else:
            print("error downloaded video is faulty.. Retrying to download")
            download_video(url,filename)

def downloader(course,quality):
    course_name = course["name"]
    course_file = course["files"]
    preview_id = course["trailer_jwplayer_id"]
    publish_state = course["status"]
    if(publish_state == "published"):
        course_meta = course['content']
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
        if(preview_id != ""):
            course_preview = course_preview_meta_getter(preview_id,quality)
            download_video(course_preview[1],course_preview[0])
        with tqdm(total=len(course_meta)) as pbar:
            for i in course_meta:
                pbar.set_description("Downloading: %s" % course_name)
                if i["content_type"] == "group":
                    if not os.path.exists(i["name"]):
                        os.makedirs(i["name"])
                    os.chdir(i["name"])
                    for j in i["content"]:
                        if(j["content_type"] == "topic"):
                            if not os.path.exists(j["name"]):
                                os.makedirs(j["name"])
                            os.chdir(j["name"])
                            for k in j["content"]:
                                if(k["content_type"] == "video"):
                                    out = get_meta(k["uuid"],quality)
                                    download_video(out[1],out[0])
                            os.chdir('../')
                    os.chdir('../')
                else:
                    print("The content type is not a group")
                pbar.update(1)
        os.chdir('../')
        print("Course downloaded successfully\n")
    else:
        print("This course is marked as {}. Visit later when available on website to download ".format(publish_state))


if __name__ == '__main__':
    os.system('clear')
    print("INE Courses Downloader\n")
    if(len(access_token) == 0):
        print("Please refer to readme.md in github and set the access_token")
        exit()
    if(len(access_token) != 1009):
        print("Access token entered is faulty. Check for and correct errors!")
        exit()
    if(len(refresh_token) == 0):
        print("Please refer to readme.md in github and set the refresh_token")
        exit()
    if(len(refresh_token) != 1784):
        print("Refresh token entered is faulty. Check and correct errors!")
        exit()
    print("Warning! Until the script completes execution do not access INE website or mobile app\n as it might invalidate the session!\n")
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
        print("\nInitializing for Site dump\n")
        total_course = len(all_courses)
        course_batch = 20
        if (os.path.isfile(course_completed_path)):
            with open(course_completed_path,'r') as cc:
                completed_course = int(cc.readline()) + 1
        else:
            completed_course = 0
        for i in range(completed_course,total_course):
            print("Course NO:",i)
            if(i % course_batch == 0 and i != 0):
                print('Course batch complete \nWaiting 1 minute before resuming')
                access_token_refetch()
                sleep(60)
            course = all_courses[i]
            if(course["access"]["related_passes"][0]["name"] in access_pass):
                downloader(course,quality)
                update_downloaded(str(i))
            else:
                print("Your pass does not allow access to this course\n skipping this course..\n")
        os.remove(course_completed_path)
        print("Site rip is done!\n")


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
            if(course["access"]["related_passes"][0]["name"] in access_pass):
                downloader(course,quality)
            else:
                print("You do not have the subscription pass access to this course")
                exit()

        elif(choice == 2):
            choice = int(input("Please enter the number corresponding to the course you would like to download\n"))
            course = all_courses[choice]
            if(course["access"]["related_passes"][0]["name"] in access_pass):
                downloader(course,quality)
            else:
                print("You do not have the subscription pass to access to this course")
                exit()
        else:
            exit("Invalid choice!\n")