"""
Version: 1.3.7 Stable release
Author: Jayapraveen AR
Credits: @Dexter101010
Program Aim: To download courses from INE website for personal and educational use
Location : India
Date : 26/02/2021
To Do:
3. Optimize for efficiency and memory footprint
5. Compile the endpoints and data handling logic to prevent abuse and protect the authenticity of this script
8. Move all configurations to seperate configuration file
10. Make more autonomous with cli invocation and args parsing
Bug reporting: Please report them if any in issues tab
"""

import requests,json,os,re,shutil,getpass,multiprocessing,sys
from time import sleep
from tqdm import tqdm
#script location
script_path = os.getcwd()
token_path = script_path + '/ine_tokens.txt'
course_completed_path = script_path + '/ine_completed_course.txt'
course_list_path = script_path + '/ine_courses.txt'
#Download location
custom = False
save_path = "download_location" if(custom) else os.getcwd()
#headers
accept = "application/json, text/plain, */*"
x_requested_with = "com.my.ine"
sec_fetch_site = "cross-site"
sec_fetch_mode = "cors"
sec_fetch_dest = "empty"
content_type = "application/json;charset=UTF-8"
user_agent = "Mozilla/5.0 (Linux; Android 6.0;PIXEL XL Build/INE) Mobile Safari/537.29"
referer = "http://localhost"
origin = "file://"
accept_encodings = "gzip, deflate, br"
#endpoints
login_url = "https://uaa.ine.com/uaa/authenticate"
all_courses_url = "https://content-api.rmotr.com/api/v1/courses?active=true&page_size=none&ordering=-created"
video_url = "https://video.rmotr.com/api/v1/videos/{}/media"
subscription_url = "https://subscriptions.ine.com/subscriptions/subscriptions?embed=passes"
passes_url = "https://subscriptions.ine.com/subscriptions/passes?embed=learning_areas"
refresh_token_url = "https://uaa.ine.com/uaa/auth/refresh-token"
auth_check_url = "https://uaa.ine.com/uaa/auth/state/status"
preview_url = "https://content.jwplatform.com/v2/media/"
#Retry times
retry = 4

def login():
    global access_token
    global refresh_token
    host = "uaa.ine.com"
    header = {"Host": host,"Origin": origin,"Referer": referer,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    user_name = input("Enter your Username: ")
    password = getpass.getpass(prompt="Enter your Password: \n")
    login_data = {"username": user_name,"password": password}
    login_data = json.dumps(login_data)
    login_data = requests.post(login_url,headers = header,data = login_data)
    if(login_data.status_code == 200):
        login_data = json.loads(login_data.text)
        access_token = login_data["data"]["tokens"]["data"]["Bearer"]
        refresh_token = login_data["data"]["tokens"]["data"]["Refresh"]
        with open(token_path,'w') as fp:
            tokens = {"access_token": access_token,"refresh_token": refresh_token}
            fp.write(json.dumps(tokens))
            access_token = "Bearer "+ access_token
            auth_check()
    elif(login_data.status_code == 403):
        print("Username or password is incorrect\n ")
        option = int(input("Choose from the following options:\n1.Relogin\n2.Exit\n"))
        if(option == 1):
            login()
        else:
            exit()

def auth_check():
    global access_token
    global refresh_token
    host = "uaa.ine.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    auth_valid = requests.get(auth_check_url,headers = header)
    if(auth_valid.status_code == 200):
        user = json.loads(auth_valid.text)
        if(user["data"]["email"]):
            email = user["data"]["email"]
            fname = user["data"]["profile"]["data"]["first_name"]
            lname = user["data"]["profile"]["data"]["last_name"]
            print("Logged in to INE as {} {} with {}\n".format(fname,lname,email))
        # take new access token
        if "meta" in user:
            if "tokens" in user["meta"]:
                access_token = user["meta"]["tokens"]["Bearer"]
                with open(token_path,'w') as fp:
                    print("access_token: " + access_token)
                    print("refresh_token: " + refresh_token)
                    tokens = {"access_token": access_token,"refresh_token": refresh_token}
                    fp.write(json.dumps(tokens))

    else:
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
        out = json.loads(out.text)
        access_token = out["data"]["tokens"]["data"]["Bearer"]
        refresh_token = out["data"]["tokens"]["data"]["Refresh"]
        with open(token_path,'w') as fp:
            tokens = {"access_token": access_token,"refresh_token": refresh_token}
            fp.write(json.dumps(tokens))
        access_token = "Bearer "+ access_token
        print("Got new tokens")
    elif(out.status_code == 401):
        relogin = int(input("Failure, Please choose from the following options\n1.Login\n2.Recheck for updated tokens(after updating the tokens in the file)\n3.Exit\n"))
        if(relogin == 1):
            login()
        elif(relogin == 2):
            auth_check()
        elif(relogin == 3):
            exit()

def update_downloaded(course_index):
    with open(course_completed_path,'w') as cci:
        cci.write(course_index)

def course_has_access(course):
    for passes in range(len(course["access"]["related_passes"]) -1 ,0,-1):
        boolean =  True if course["access"]["related_passes"][passes]["name"] in access_pass else False
        if(boolean):
            break
    return boolean

def course_preview_meta_getter(preview_id,quality):
    video_preview_url = preview_url + preview_id
    video = requests.get(video_preview_url)
    video = json.loads(video.text)
    try:
        if(video["message"].split(':')[-1] == " id not found in index."):
            out = [0]
            return out
    except:
        pass
    out = []
    title = video["title"] + '.mp4'
    if os.name == 'nt':
        title = re.sub("[^0-9a-zA-Z.]+", "", title)
    out.append(title)
    video_list = video["playlist"][0]["sources"]
    video,video_quality = 0,0
    for i in video_list:
        try:
            if(i["height"] > video_quality):
                next_quality_video = video
                video_quality = i["height"]
                video = i["file"]
        except:
            continue
    out.append(video) if (quality == 1) else out.append(next_quality_video)
    return out


def pass_validator(sub_url = subscription_url,epoch = 0):
    global siterip
    if(epoch == 2):
        exit("No Subscription found! Program cannot proceed further..")
    host = "subscriptions.ine.com"
    header = {"Host": host,"Origin": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Referer": referer}
    passes = requests.get(sub_url,headers = header)
    if(passes.status_code == 200):
        passes = json.loads(passes.text)
        if(len(passes["data"])):
            pass_avail = []
            try:
                siterip = 1
                passes = passes["data"][0]["passes"]["data"]
                for i in passes:
                    pass_avail.append(i["name"])
                    pass_avail.append("INE " + i["name"])
            except:
                siterip = 0
                print("Free Subscription Detected! Do not enter courses not accessible with your account... \n")
                passes = passes["data"]
                for passinfo in passes:
                    pass_avail.append(passinfo.get("name",None))
                    pass_avail.append("INE " + passinfo.get("name",0))
        else:
            print("No subscriptions found in your account! Checking for Passes..\n")
            pass_avail = pass_validator(passes_url,epoch + 1)
    elif(passes.status_code == 500):
        exit("Ine Subscriptions Server error\n")
    return pass_avail


def sanitize(course_name):
    if(course_name.split(':')[0] == "Video"):
        course_name = course_name.split('/')[-1]
        course_name = re.sub('/',' ',course_name)
        if os.name == 'nt':
            course_name = re.sub("[^0-9a-zA-Z.\s]+", "", course_name)
        return course_name
    else:
        course_name = re.sub('/',' ',course_name)
        if os.name == 'nt':
            course_name = re.sub("[^0-9a-zA-Z\s]+", "", course_name)
        return course_name + '.mp4'

#Video metadata getter
def get_meta(uuid):
    host = "video.rmotr.com"
    header = {"Host": host,"Origin": referer,"Referer": referer,"Authorization": access_token,"User-Agent": user_agent,"Accept": accept,"X-Requested-With": x_requested_with,"Accept-Encoding": accept_encodings,"sec-fetch-mode": sec_fetch_mode,"sec-fetch-dest": sec_fetch_dest,"Content-Type": content_type}
    out = requests.get(video_url.format(uuid),headers = header)
    if out.status_code == 200:
        out = json.loads(out.text)
        name = sanitize(out["title"])
        subtitle,video,maxquality,nextquality = 0,0,0,0
        for i in out["playlist"][0]["sources"]:
            try:
                if(i["height"] > maxquality):
                    nextvideo = video
                    video = i["file"]
            except:
                continue
        if (quality == 1):
            video = video
        else:
            video = nextvideo
        for i in out["playlist"][0]["tracks"]:
            if(i["kind"] == "captions"):
                subtitle = i["file"]
        out = []
        out.append(name)
        out.append(video)
        if (subtitle):
            out.append(subtitle)
        return out
    elif(out.status_code == 403):
        print("No access to video metadata;\nToken expired. Trying to refresh ..")
        access_token_refetch()
        print("Resuming operations..")
        return get_meta(uuid)


def coursemeta_fetcher():
    all_courses = requests.get(all_courses_url)
    with open(course_list_path,'w', encoding ='utf8') as course_handler:
        course_handler.write(all_courses.text)

def total_courses():
    with open(course_list_path,'r', encoding ='utf8') as course_handler:
        all_courses = json.loads(course_handler.read())
    length = len(all_courses)
    count = 0
    for i in all_courses:
        print("{}. {}".format(count,i["name"]))
        count = count + 1
    print ("Total {} courses\n".format(length))
    return all_courses

def download_video(url,filename,epoch = 0):
    if(os.path.isfile(filename)):
        #print(video_head.text,video_head.status_code,video_head.headers,url,filename)
        video_head = requests.head(url, allow_redirects = True)
        if video_head.status_code == 200:
            video_length = int(video_head.headers.get("content-length"))
            if(os.path.getsize(filename) >= video_length):
                print("Video already downloaded.. skipping Downloading..")
            else:
                print("Redownloading faulty download..")
                os.remove(filename) #Improve removing logic
                download_video(url,filename)
        else:
            if (epoch > retry):
                exit("Server doesn't support HEAD.")
            download_video(url,filename,epoch + 1)
    else:
        video = requests.get(url, stream=True)
        video_length = int(video.headers.get("content-length"))
        if video.status_code == 200:
            if(os.path.isfile(filename) and os.path.getsize(filename) >= video_length):
                print("Video already downloaded.. skipping write to disk..")
            else:
                try:
                    with open(filename, 'wb') as video_file:
                        shutil.copyfileobj(video.raw, video_file)
                except:
                    print("Connection error: Reattempting download of video..")
                    download_video(url,filename, epoch + 1)

            if os.path.getsize(filename) >= video_length:
                pass
            else:
                print("Error downloaded video is faulty.. Retrying to download")
                download_video(url,filename, epoch + 1)
        else:
            if (epoch > retry):
                exit("Error Video fetching exceeded retry times.")
            print("Error fetching video file.. Retrying to download")
            download_video(url,filename, epoch + 1)


def download_subtitle(title,url):
    if(title.split('.')[-1] not in ['zip','rar']):
        title = title.split('.')
        title = title[0] + '.' + title[-2] + ".srt"
    url = requests.get(url, stream = True, allow_redirects = True)
    if (url.status_code == 200):
        try:
            with open(title, 'wb') as subtitle:
                shutil.copyfileobj(url.raw, subtitle)
        except:
            print("Connection error: Reattempting download of subtitiles..")
            download_subtitle(url,title)

def downloader(course):
    course_name = course["name"]
    if os.name == 'nt':
        course_name = re.sub("[^0-9a-zA-Z]+", "", course_name)
    course_files = course["files"]
    preview_id = course["trailer_jwplayer_id"]
    publish_state = course["status"]
    if(publish_state == "published"):
        course_meta = course['content']
        os.chdir(save_path)
        if not os.path.exists(course_name):
            os.makedirs(course_name)
        os.chdir(course_name)
        if(len(course_files) > 0):
            filespbar = tqdm(course_files, unit='file', unit_scale=True)
            for i in filespbar:
                filespbar.set_description("Downloading course file: %s" % i["name"])
                course_file = requests.get(i["url"])
                if(i["name"].split('.')[-1] not in ["zip","pdf"]):
                    i["name"] = i["name"] + '.zip'
                open(i["name"], 'wb').write(course_file.content)
                filespbar.update(1)
        if(preview_id != ""):
            course_preview = course_preview_meta_getter(preview_id,quality)
            if(course_preview[0] != 0):
                download_video(course_preview[1],course_preview[0])
        folder_index = 1
        coursepbar = tqdm(course_meta, unit="course", unit_scale=True)
        for i in coursepbar:
            coursepbar.set_description("Downloading: %s" % course_name)
            if i["content_type"] == "group":
                folder_name = str(folder_index) + '.' +i["name"]
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                os.chdir(folder_name)
                folder_index = folder_index + 1
                subfolder_index = 1
                for j in i["content"]:
                    if(j["content_type"] == "topic"):
                        subfolder_name = str(subfolder_index) + '.' + j["name"]
                        if not os.path.exists(subfolder_name):
                            os.makedirs(subfolder_name)
                        os.chdir(subfolder_name)
                        subfolder_index = subfolder_index + 1
                        video_index = 1
                        with tqdm(j["content"], unit='videofile', unit_scale=True) as pbar:
                            for k in pbar:
                                #print(k)
                                if(k["content_type"] == "video"):
                                    out = get_meta(k["uuid"])
                                    out[0] = str(video_index) + '.' + out[0]
                                    pbar.set_description("Downloading: %s" %out[0])
                                    video_index = video_index + 1
                                    download_video(out[1],out[0])
                                    try:
                                        if(out[2]):
                                            download_subtitle(out[0],out[2])
                                    except:
                                        pass
                                    pbar.update()
                            os.chdir('../')

                os.chdir('../')
            else:
                print("The content type is not a group")
            coursepbar.update()
        os.chdir('../')
        print("Course downloaded successfully\n")
    else:
        print("This course is marked as {}. Visit later when available on website to download ".format(publish_state))


if __name__ == '__main__':
    if not (sys.version_info.major == 3 and sys.version_info.minor >= 6):
        print("This script requires Python 3.6 or higher!")
        exit("You are using Python {}.{}".format(sys.version_info.major, sys.version_info.minor))
    os.system('cls') if os.name == 'nt' else os.system('clear')
    print("INE Courses Downloader\n")
    if(os.path.isfile(token_path)):
        with open(token_path,'r') as fp:
            try:
                fp = json.loads(fp.read())
                access_token = fp["access_token"]
                refresh_token = fp["refresh_token"]
                access_token = "Bearer "+ access_token
            except:
                print("Please check the data in token file and correct for errors")
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
        auth_check()
    else:
        login()
    print("Warning! Until the script completes execution do not access INE website or mobile app\n as it might invalidate the session!\n")
    access_pass = pass_validator()
    method = int(input("Choose Method Of Operation: \n1.Site Rip \n2.Select Individual Course\n")) if siterip else 2
    if (os.path.isfile(course_list_path)):
        all_courses = total_courses()
    else:
        coursemeta_fetcher()
        all_courses = total_courses()
    quality = int(input("Choose Preferred Video Quality\n1.Highest Available Quality (1080p)\n2.Next To Highest Quality (720p)\n"))
    if(method == 1):
        cons = input("Warning! This is a high compute and throughput functionality and needs\nlots and lots of compute time and storage space \nEnter \"I agree\" to acknowledge and proceed!\n")
        if(cons.lower() != "i agree"):
            print("User did not accept! Program exiting")
            exit()
        print("\nInitializing for Site dump\n")
        total_course = len(all_courses)
        course_batch = multiprocessing.cpu_count() // 2
        if (os.path.isfile(course_completed_path)):
            with open(course_completed_path,'r') as cc:
                completed_course = int(cc.readline()) + 1
        else:
            completed_course = 0
        for i in range(completed_course,total_course,course_batch):
            if(i + course_batch > total_course):
                this_session = (i + course_batch) - total_course
            else:
            	this_session = i + course_batch
            cpbar = tqdm(total = course_batch)
            print("\nCourses to be downloaded this batch:",i," to ",this_session)
            pool = multiprocessing.Pool(multiprocessing.cpu_count())  # Num of CPUs
            with pool as p:
                p.map(downloader,(all_courses[j] for j in range(i, this_session) if (False if (len(all_courses[j]["access"]["related_passes"]) == 0) else True if (course_has_access(all_courses[j])) else False) and 1 or print("Course not in subscription access pack. Skipping ..")))
                p.close()
                p.join()
            update_downloaded(str(i))
            print("\nCourse batch successfully completed downloading.. Starting Next batch..")
            sleep(1)
        os.remove(course_completed_path)
        print("Site rip is done!\n")

    else:
        print("Free Subscription Detected! Do not enter courses not accessible with your account...\n") if siterip == 0 else 0
        choice = int(input("Choose Method Of Selecting Course\n1.Enter url\n2.Choose from the above listed course\n3.Download a select number of courses from the above list\n4.Download a bunch of courses from the above list using a range\n"))
        if(choice == 1):
            url = input("Paste the url\n")
            flag = 1
            try:
                for i in all_courses:
                    if(i["url"] == url):
                        choice = i
                        flag = 0
                if(flag == 1):
                    raise Exception
            except:
                print('Course not found,Recheck url or Choose other method for selecting course\n')
                exit()
            course = choice
            if(course_has_access(course)):
                downloader(course)
            else:
                 exit("You do not have the subscription pass access to this course")

        elif(choice == 2):
            choice = int(input("Please enter the number corresponding to the course you would like to download\n"))
            course = all_courses[choice]
            if(course_has_access(course)):
                downloader(course)
            else:
                exit("You do not have the subscription/pass to access to this course")
        elif(choice == 3):
            print("Enter the course numbers to download. Enter \"Done\" to Finish entering courses")
            course_list = []
            while(True):
                choice = input()
                if(choice.lower() == "done"):
                    break
                else:
                    if (0 <= int(choice) <= len(all_courses)):
                        course_list.append(int(choice))
                    else:
                        print("Invalid Choice")
                        continue
            for course_select in course_list:
                course = all_courses[course_select]
                if(course_has_access(course)):
                    downloader(course)
                else:
                    print("You do not have the subscription/pass to access to this course")
                    continue
        elif(choice == 4):
            lowerlimit = int(input("Enter the starting course number(Inclusive)\n"))
            upperlimit = int(input("Enter the closing course number(Inclusive)\n"))
            if(lowerlimit < 0 or lowerlimit > len(all_courses) -1):
                exit("Invalid lower limit..")
            if(upperlimit < 0 or upperlimit > len(all_courses) -1):
                exit("Invalid upper limit..")
            for course_select in range(lowerlimit,upperlimit + 1):
                course = all_courses[course_select]
                if(course_has_access(course)):
                    downloader(course)
                else:
                    print("You do not have the subscription/pass to access to this course")
                    continue
        else:
            exit("Invalid choice!\n")
