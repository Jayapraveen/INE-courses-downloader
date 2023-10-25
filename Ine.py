"""
Version: 1.3.9 Stable release
Original Author: Jayapraveen AR, Pi
Credits: @Dexter101010
Program Aim: To download courses from INE website for personal and educational use
Location : India
Date : 21/10/2023
To Do:
1. Rework the siterip mode (temporary workaround is download range (0 - last course nr)
3. Optimize for efficiency and memory footprint
5. Compile the endpoints and data handling logic to prevent abuse and protect the authenticity of this script
8. Move all configurations to seperate configuration file
10. Make more autonomous with cli invocation and args parsing
Bug reporting: Please report them if any in issues tab
"""

import requests, json, os, re, shutil, getpass, sys
from time import sleep
from tqdm import tqdm

# script location
script_path = os.getcwd()
token_path = script_path + '/ine_tokens.txt'
course_completed_path = script_path + '/ine_completed_course.txt'
course_list_path = script_path + '/ine_courses.txt'
course_list_index = script_path + '/ine_courses_index.txt'
# Download location
custom = False
# headers
referer = "http://localhost"
host = 'uaa.ine.com'
sec_Ch_Ua = '"Not=A?Brand";v="99", "Chromium";v="118"'
accept = 'application/json'
content_Type = 'application/json;charset=UTF-8'
sec_Ch_Ua_Mobile = '?0'
user_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.88 Safari/537.36'
sec_Ch_Ua_Platform = '"Windows"'
origin = 'https://my.ine.com'
sec_Fetch_Site = 'same-site'
sec_Fetch_Mode = 'cors'
sec_Fetch_Dest = 'empty'
accept_Encoding = 'gzip, deflate, br'
# endpoints
login_url = "https://uaa.ine.com/uaa/authenticate"
all_courses_url = "https://content-api.rmotr.com/api/v1/courses?active=true&page_size=none&ordering=-created"
video_url = "https://video.rmotr.com/api/v1/videos/{}/media"
subscription_url = "https://subscriptions.ine.com/subscriptions/subscriptions?embed=passes"
passes_url = "https://subscriptions.ine.com/subscriptions/passes?embed=learning_areas"
refresh_token_url = "https://uaa.ine.com/uaa/auth/refresh-token"
auth_check_url = "https://uaa.ine.com/uaa/auth/state/status"
preview_url = "https://content.jwplatform.com/v2/media/"
content_url = "https://content-api.ine.com/api/v1/iframes/{}/media"
lab_url = "https://content-api.rmotr.com/api/v1/labs/{}"
labimage_url = "https://assets.ine.com/cybersecurity-lab-images/{}/image{}.png"
slide_url = "https://els-cdn.content-api.ine.com/{}/"
file_url = "https://file.rmotr.com/api/v1/files/{}/download"
slidejs_url = slide_url + "data/slide{}.js"
slidecss_url = slide_url + "data/slide{}.css"
slideimg_url = slide_url + "data/img{}.png"
slidefnt_url = slide_url + "data/fnt{}.woff"

# Retry times
retry = 10


def login():
    global access_token
    header = {
        "Host": host,
        "Sec-Ch-Ua": sec_Ch_Ua,
        "Accept": accept,
        "Content-Type": content_Type,
        "Sec-Ch-Ua_mobile": sec_Ch_Ua_Mobile,
        "User-Agent": user_Agent,
        "Sec-Ch-Ua-Platform": sec_Ch_Ua_Platform,
        "Origin": origin,
        "Sec-Fetch-Site": sec_Fetch_Site,
        "Sec-Fetch-Mode": sec_Fetch_Mode,
        "Sec-Fetch-Dest": sec_Fetch_Dest,
        "Accept-Encoding": accept_Encoding
    }
    user_name = input("Enter your Username: ")
    password = getpass.getpass(prompt="Enter your Password: \n")
    login_data = {"username": user_name, "password": password}
    login_data = json.dumps(login_data)
    login_data = requests.post(login_url, headers=header, data=login_data)
    if (login_data.status_code == 200):
        login_data = json.loads(login_data.text)
        access_token = login_data['data']["tokens"]["data"]["Bearer"]
        with open(token_path, 'w') as fp:
            token = {"access_token": access_token}
            fp.write(json.dumps(token))
            access_token = "Bearer " + access_token
            auth_check()
    elif (login_data.status_code == 403):
        print("Username or password is incorrect\n ")
        option = int(input("Choose from the following options:\n1.Relogin\n2.Exit\n"))
        if (option == 1):
            login()
        else:
            exit()


def auth_check():
    global access_token
    host = "uaa.ine.com"
    header = {
        "Host": host,
        "Origin": referer,
        "Referer": referer,
        "Authorization": access_token,
        "User-Agent": user_Agent,
        "Accept": accept,
        "Accept-Encoding": accept_Encoding,
        "sec-fetch-mode": sec_Fetch_Mode,
        "sec-fetch-dest": sec_Fetch_Dest,
        "Content-Type": content_Type
    }
    auth_valid = requests.get(auth_check_url, headers=header)
    if (auth_valid.status_code == 200):
        user = json.loads(auth_valid.text)
        if (user["data"]["email"]):
            email = user["data"]["email"]
            fname = user["data"]["profile"]["data"]["first_name"]
            lname = user["data"]["profile"]["data"]["last_name"]
            print("Logged in to INE as {} {} with {}\n".format(fname, lname, email))
        # take new access token
        if "meta" in user:
            if "tokens" in user["meta"]:
                access_token = user["meta"]["tokens"]["Bearer"]
                with open(token_path, 'w') as fp:
                    print("access_token: " + access_token)
                    token = {"access_token": access_token}
                    fp.write(json.dumps(token))

    else:
        print("Access token expired!\nPlease login")
        login()


def update_downloaded(course_index):
    with open(course_completed_path, 'w') as cci:
        cci.write(course_index)


def course_has_access(course):
    for passes in range(len(course["access"]["related_passes"]) - 1, 0, -1):
        boolean = True if course["access"]["related_passes"][passes]["id"] in access_pass else False
        if (boolean):
            break
    return boolean


def course_preview_meta_getter(preview_id, quality):
    video_preview_url = preview_url + preview_id
    video = requests.get(video_preview_url)
    video = json.loads(video.text)
    try:
        if (video["message"].split(':')[-1] == " id not found in index."):
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
    video, video_quality = 0, 0
    for i in video_list:
        try:
            if (i["height"] > video_quality):
                next_quality_video = video
                video_quality = i["height"]
                video = i["file"]
        except:
            continue
    out.append(video) if (quality == 1) else out.append(next_quality_video)
    return out


def pass_validator(sub_url=subscription_url, epoch=0):
    global siterip
    if (epoch == 2):
        exit("No Subscription found! Program cannot proceed further..")
    host = "subscriptions.ine.com"
    header = {
        "Host": host,
        "Origin": referer,
        "Referer": referer,
        "Authorization": access_token,
        "User-Agent": user_Agent,
        "Accept": accept,
        "Accept-Encoding": accept_Encoding,
        "sec-fetch-mode": sec_Fetch_Mode,
        "sec-fetch-dest": sec_Fetch_Dest,
        "Content-Type": content_Type
    }
    passes = requests.get(sub_url, headers=header)
    if (passes.status_code == 200):
        passes = json.loads(passes.text)
        if (len(passes["data"])):
            pass_avail = []
            try:
                siterip = 1
                passes = passes["data"][0]["passes"]["data"]
                for i in passes:
                    pass_avail.append(i["content_pass_id"])
            except:
                siterip = 0
                print("Free Subscription Detected! Do not enter courses not accessible with your account... \n")
                passes = passes["data"]
                for passinfo in passes:
                    pass_avail.append(passinfo.get("name", None))
                    pass_avail.append("INE " + passinfo.get("name", 0))
        else:
            print("No subscriptions found in your account! Checking for Passes..\n")
            pass_avail = pass_validator(passes_url, epoch + 1)
    elif (passes.status_code == 500):
        exit("Ine Subscriptions Server error\n")
    return pass_avail


def sanitize(course_name):
    if (course_name.split(':')[0] == "Video"):
        course_name = course_name.split('/')[-1]
        course_name = re.sub('/', ' ', course_name)
        if os.name == 'nt':
            course_name = re.sub("[^0-9a-zA-Z.\s]+", "", course_name)
        return course_name
    else:
        course_name = re.sub('/', ' ', course_name)
        if os.name == 'nt':
            course_name = re.sub("[^0-9a-zA-Z\s]+", "", course_name)
        return course_name + '.mp4'


# Video metadata getter
def get_meta(uuid, course_id):
    host = "video.rmotr.com"
    header = {
        'Host': host,
        'Sec-Ch-Ua': '"Not=A?Brand";v="99", "Chromium";v="118"',
        'Accept': 'application/json',
        'Sec-Ch-Ua-Mobile': '?0',
        'Authorization': access_token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.88 Safari/537.36',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Origin': 'https://my.ine.com',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    out = requests.get(video_url.format(uuid) + f'?parent_type=course&parent_id={course_id}', headers=header)
    if out.status_code == 200:
        out = json.loads(out.text)
        name = sanitize(out["title"])
        subtitle, video, maxquality, nextquality = 0, 0, 0, 0
        for i in out["playlist"][0]["sources"]:
            try:
                if (i["height"] > maxquality):
                    nextvideo = video
                    video = i["file"]
            except:
                continue
        if (quality == 1):
            video = video
        else:
            video = nextvideo
        for i in out["playlist"][0]["tracks"]:
            if (i["kind"] == "captions"):
                subtitle = i["file"]
        out = []
        out.append(name)
        out.append(video)
        if (subtitle):
            out.append(subtitle)
        return out
    elif (out.status_code == 403):
        print("No access to video metadata;\nToken expired. Please login again ..")
        login()
        print("Resuming operations..")
        return get_meta(uuid, course_id)


def coursemeta_fetcher():
    all_courses = requests.get(all_courses_url)
    with open(course_list_path, 'w', encoding='utf8') as course_handler:
        course_handler.write(all_courses.text)


def total_courses():
    with open(course_list_path, 'r', encoding='utf8') as course_handler:
        all_courses = json.loads(course_handler.read())
    length = len(all_courses)
    count = 0
    open(course_list_index, 'w').close()
    for i in all_courses:
        print("{}. {}".format(count, i["name"]))
        with open(course_list_index, 'a', encoding='utf8') as course_handler:
            course_handler.write("{}. {}\n".format(count, i["name"]))
        count = count + 1
    print("Total {} courses\n".format(length))
    return all_courses


def download_lab(uuid, lab_index):
    # content meta
    host = "content-api.rmotr.com"
    header = {
        "Host": host,
        "Origin": referer,
        "Referer": referer,
        "Authorization": access_token,
        "User-Agent": user_Agent,
        "Accept": accept,
        "Accept-Encoding": accept_Encoding,
        "sec-fetch-mode": sec_Fetch_Mode,
        "sec-fetch-dest": sec_Fetch_Dest,
        "Content-Type": content_Type
    }
    out = requests.get(lab_url.format(uuid), headers=header)
    data = json.loads(out.text)

    # prepare subfolders
    subfolder_name = ('Lab' + str(lab_index) + '.' + data["name"]).replace(':', ';').replace('/', '').strip()
    if not os.path.exists(subfolder_name):
        os.makedirs(subfolder_name)
    if not os.path.exists(subfolder_name + "/data"):
        os.makedirs(subfolder_name + "/data")

    # save lab description as html
    with open(subfolder_name + "/index.html", 'w', encoding='utf8') as fp:
        html_out = data["description_html"]
        # replace external assets links
        link = "https://assets.ine.com/cybersecurity-lab-images/" + uuid
        html_out = html_out.replace(link, "data")
        fp.write(html_out)

    # imageX.png
    host = "assets.ine.com"
    header = {
        "Host": host,
        "Origin": referer,
        "Referer": referer,
        "Authorization": access_token,
        "User-Agent": user_Agent,
        "Accept": accept,
        "Accept-Encoding": accept_Encoding,
        "sec-fetch-mode": sec_Fetch_Mode,
        "sec-fetch-dest": sec_Fetch_Dest,
        "Content-Type": content_Type
    }
    slide_number = 1
    status = True
    while status:
        out = requests.get(labimage_url.format(uuid, str(slide_number)), headers=header, stream=True)
        if (out.status_code == 200):
            with open(subfolder_name + "/data/image{}.png".format(str(slide_number)), 'wb') as fp:
                shutil.copyfileobj(out.raw, fp)
            slide_number = slide_number + 1
        else:
            status = False


def download_slides(uuid, slide_index):
    # content meta
    host = "content-api.ine.com"
    header = {
        "Host": host,
        "Origin": referer,
        "Referer": referer,
        "Authorization": access_token,
        "User-Agent": user_Agent,
        "Accept": accept,
        "Accept-Encoding": accept_Encoding,
        "sec-fetch-mode": sec_Fetch_Mode,
        "sec-fetch-dest": sec_Fetch_Dest,
        "Content-Type": content_Type
    }
    out = requests.get(content_url.format(uuid), headers=header)
    if (out.status_code == 200):

        cookies = out.cookies.get_dict()
        data = json.loads(out.text)

        # prepare subfolders
        subfolder_name = str(slide_index) + '.' + data["name"] + '/'
        if not os.path.exists(subfolder_name):
            os.makedirs(subfolder_name)
        if not os.path.exists(subfolder_name + "/data"):
            os.makedirs(subfolder_name + "/data")

        # files
        host = "file.rmotr.com"
        header = {
            "Host": host,
            "Origin": referer,
            "Referer": referer,
            "Authorization": access_token,
            "User-Agent": user_Agent,
            "Accept": accept,
            "Accept-Encoding": accept_Encoding,
            "sec-fetch-mode": sec_Fetch_Mode,
            "sec-fetch-dest": sec_Fetch_Dest,
            "Content-Type": content_Type
        }
        for f in data["files"]:
            out = requests.get(file_url.format(f), headers=header)
            if (out.status_code == 200):
                file_data = json.loads(out.text)
                dl_url = file_data["download_url"]
                file_name = file_data["filename"]
                out = requests.get(dl_url, stream=True)
                if (out.status_code == 200):
                    file_name = file_name.replace('/', '_')
                    with open(subfolder_name + file_name, 'wb') as fp:
                        shutil.copyfileobj(out.raw, fp)

        # prepare header for slide content download
        host = "els-cdn.content-api.ine.com"
        header = {
            "Host": host,
            "Origin": referer,
            "Referer": referer,
            "Authorization": access_token,
            "User-Agent": user_Agent,
            "Accept": accept,
            "Accept-Encoding": accept_Encoding,
            "sec-fetch-mode": sec_Fetch_Mode,
            "sec-fetch-dest": sec_Fetch_Dest,
            "Content-Type": content_Type
        }

        # index.html
        if not os.path.exists(subfolder_name + "index.html"):
            out = requests.get(data["url"], headers=header, cookies=cookies)
            if (out.status_code == 200):
                with open(subfolder_name + "index.html", 'w') as fp:
                    # remove ending after ".js"
                    html_out = out.text
                    pre = "\<script\ src\=\""
                    suf = "\"\>\<\/script\>"
                    js_files = re.findall(pre + ".*" + suf, html_out)
                    for js in js_files:
                        js_path = re.findall('"([^"]*)"', js)[0]
                        html_out = html_out.replace(js_path, js_path[:js_path.rfind('?')])
                    fp.write(html_out)

                # browsersupport.js and player.js
                pre = "\<script\ src\=\""
                suf = "\"\>\<\/script\>"
                js_files = re.findall(pre + ".*" + suf, out.text)
                for js in js_files:
                    js_path = re.findall('"([^"]*)"', js)[0]
                    out = requests.get(slide_url.format(uuid) + js_path, headers=header, cookies=cookies)
                    if (out.status_code == 200):
                        with open(subfolder_name + js_path[:js_path.rfind('?')], 'w') as fp:
                            fp.write(out.text)

        # slideX.js
        num = 1
        http = True
        while http:
            target = subfolder_name + "data/slide{}.js".format(str(num))
            if os.path.exists(target):
                num = num + 1
            else:
                out = requests.get(slidejs_url.format(uuid, str(num)), headers=header, cookies=cookies)
                if (out.status_code == 200):
                    if num == 1:
                        print('Downloading slideX.js...')
                    with open(target, 'w', encoding="utf8") as fp:
                        fp.write(out.text)
                    num = num + 1
                else:
                    http = False

        # slideX.css
        num = 1
        http = True
        while http:
            target = subfolder_name + "data/slide{}.css".format(str(num))
            if os.path.exists(target):
                num = num + 1
            else:
                out = requests.get(slidecss_url.format(uuid, str(num)), headers=header, cookies=cookies)
                if (out.status_code == 200):
                    if num == 1:
                        print('Downloading slideX.css...')
                    with open(target, 'w') as fp:
                        fp.write(out.text)
                    num = num + 1
                else:
                    http = False

        # imgX.png
        num = 0
        http = True
        while http:
            target = subfolder_name + "data/img{}.png".format(str(num))
            if os.path.exists(target):
                num = num + 1
            else:
                out = requests.get(slideimg_url.format(uuid, str(num)), headers=header, cookies=cookies, stream=True)
                if (out.status_code == 200):
                    with open(target, 'wb') as fp:
                        if num == 1:
                            print('Downloading imgX.png...')
                        shutil.copyfileobj(out.raw, fp)
                    num = num + 1
                else:
                    http = False

        # fntX.woff
        num = 0
        http = True
        while http:
            target = subfolder_name + "data/fnt{}.woff".format(str(num))
            if os.path.exists(target):
                num = num + 1
            else:
                out = requests.get(slidefnt_url.format(uuid, str(num)), headers=header, cookies=cookies, stream=True)
                if (out.status_code == 200):
                    with open(target, 'wb') as fp:
                        if num == 1:
                            print('Downloading fntX.woff...')
                        shutil.copyfileobj(out.raw, fp)
                    num = num + 1
                else:
                    http = False


def download_video(url, filename, epoch=0):
    if (os.path.isfile(filename)):
        # print(video_head.text,video_head.status_code,video_head.headers,url,filename)
        video_head = requests.head(url, allow_redirects=True)
        if video_head.status_code == 200:
            video_length = int(video_head.headers.get("content-length"))
            if (os.path.getsize(filename) >= video_length):
                print(f"---- {filename} already downloaded.. skipping Downloading..")
            else:
                print("Redownloading faulty download..")
                os.remove(filename)  # Improve removing logic
                download_video(url, filename)
        else:
            if (epoch > retry):
                exit("Server doesn't support HEAD.")
            sleep(7)
            download_video(url, filename, epoch + 1)
    else:
        video = requests.get(url, stream=True)
        video_length = int(video.headers.get("content-length"))
        if video.status_code == 200:
            if (os.path.isfile(filename) and os.path.getsize(filename) >= video_length):
                print(f"{filename} already downloaded.. skipping write to disk..")
            else:
                try:
                    # print(f'Downloading video: {filename}')
                    with tqdm.wrapattr(video.raw, "read", total=video_length, desc=f'Downloading video: {filename}') as raw:
                        with open(filename, 'wb') as video_file:
                            shutil.copyfileobj(raw, video_file)
                except:
                    print("Connection error: Reattempting download of video..")
                    download_video(url, filename, epoch + 1)

            if os.path.getsize(filename) >= video_length:
                pass
            else:
                print("Error downloaded video is faulty.. Retrying to download")
                download_video(url, filename, epoch + 1)
        else:
            if (epoch > retry):
                exit("Error Video fetching exceeded retry times.")
            print("Error fetching video file.. Retrying to download")
            download_video(url, filename, epoch + 1)


def download_subtitle(title, url):
    if (title.split('.')[-1] not in ['zip', 'rar']):
        title = title.split('.')
        title = title[0] + '.' + title[-2] + ".srt"
    url = requests.get(url, stream=True, allow_redirects=True)
    if (url.status_code == 200):
        try:
            with open(title, 'wb') as subtitle:
                shutil.copyfileobj(url.raw, subtitle)
        except:
            print("Connection error: Reattempting download of subtitiles..")
            download_subtitle(url, title)


def downloader(course):
    course_name = course["name"]
    course_id = course['id']
    if os.name == 'nt':
        course_name = course_name.replace(':', ';').replace('/', '').strip()
    course_files = course["files"]
    preview_id = course["trailer_jwplayer_id"]
    publish_state = course["status"]
    if (publish_state == "published"):
        print("\n>>>> Downloading course: %s <<<<" % course_name)
        os.chdir(save_path)
        if not os.path.exists(course_name):
            os.makedirs(course_name)
        os.chdir(course_name)
        if (len(course_files) > 0):
            for i in course_files:
                course_file = requests.get(i["url"])
                if (i["name"].split('.')[-1] not in ["zip", "pdf"]):
                    i["name"] = i["name"] + '.zip'
                open(i["name"], 'wb').write(course_file.content)
        if (preview_id != ""):
            course_preview = course_preview_meta_getter(preview_id, quality)
            if (course_preview[0] != 0):
                download_video(course_preview[1], course_preview[0])
        folder_index = 1
        content_count = 0
        for i in course['content']:
            content_count += 1
            if i["content_type"] == "group":
                folder_name = str(folder_index) + '.' + i["name"]
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)
                os.chdir(folder_name)
                folder_index = folder_index + 1
                subfolder_index = 1
                for j in i["content"]:
                    print("\n-- Downloading section: %s" % j['name'])
                    if (j["content_type"] == "topic"):
                        subfolder_name = (str(subfolder_index) + '.' + j["name"]).replace(':', ';').replace('/', '').strip()
                        if not os.path.exists(subfolder_name):
                            os.makedirs(subfolder_name)
                        os.chdir(subfolder_name)
                        subfolder_index = subfolder_index + 1
                        video_index = 1
                        slide_index = 1
                        lab_index = 1
                        for k in j["content"]:
                            if (k["content_type"] == "iframe"):
                                download_slides(k["uuid"], slide_index)
                                slide_index = slide_index + 1
                            if (k["content_type"] == "lab"):
                                download_lab(k["uuid"], lab_index)
                                lab_index = lab_index + 1
                            if (k["content_type"] == "video"):
                                out = get_meta(k["uuid"], course_id)
                                out[0] = str(video_index) + '.' + out[0]
                                video_index = video_index + 1
                                download_video(out[1], out[0])
                                try:
                                    if (out[2]):
                                        download_subtitle(out[0], out[2])
                                except:
                                    pass
                        os.chdir('../')
                os.chdir('../')
            else:
                print("The content type is not a group")
        os.chdir('../')
        print(f"\n>>>> {course_name} downloaded successfully <<<<\n")
    else:
        print("This course is marked as {}. Visit later when available on website to download ".format(publish_state))

def download_learning_path(path_courses,learning_path,all_courses):
    if len(path_courses) == 0:
        print(f"No courses could be found for {learning_path}, please verify your input!")
        exit()
    else:
        print(
            f"\n>> {len(path_courses) + 1} courses will be downloaded for the '{learning_path}' learning path. <<\n")


    for course_select in path_courses.values():
        course = all_courses[course_select]
        course_nbr = list(path_courses.values()).index(course_select)
        print(f'Downloading course {int(course_nbr) + 1} of {len(path_courses)}!')
        if course_has_access(course):
            downloader(course)
        else:
            print("You do not have the subscription/pass to access to this course")
            continue
    print(f"All {len(path_courses)} courses for the learning path {learning_path} have been downloaded!")


if __name__ == '__main__':
    if not (sys.version_info.major == 3 and sys.version_info.minor >= 6):
        print("This script requires Python 3.6 or higher!")
        exit("You are using Python {}.{}".format(sys.version_info.major, sys.version_info.minor))
    os.system('cls') if os.name == 'nt' else os.system('clear')
    print("INE Courses Downloader\n")
    if (os.path.isfile(token_path)):
        with open(token_path, 'r') as fp:
            try:
                fp = json.loads(fp.read())
                access_token = fp["access_token"]
                access_token = "Bearer " + access_token
            except:
                print("Please check the data in token file and correct for errors")
        if (len(access_token) == 0):
            print("Please refer to readme.md in github and set the access_token")
            exit()
        if (len(access_token) != 1078):
            print("Access token entered is faulty. Check for and correct errors!")
            exit()
        auth_check()
    else:
        login()
    print(
        "Warning! Until the script completes execution do not access INE website or mobile app\n as it might invalidate the session!\n")
    access_pass = pass_validator()
    # method = int(input("Choose Method Of Operation: \n1.Site Rip \n2.Select Individual Course\n")) if siterip else 2
    if (os.path.isfile(course_list_path)):
        all_courses = total_courses()
    else:
        coursemeta_fetcher()
        all_courses = total_courses()
    quality = int(input(
        "Choose Preferred Video Quality\n1.Highest Available Quality (1080p)\n2.Next To Highest Quality (720p)\n"))
    # if (method == 1):
    #     cons = input(
    #         "Warning! This is a high compute and throughput functionality and needs\nlots and lots of compute time and storage space \nEnter \"I agree\" to acknowledge and proceed!\n")
    #     if (cons.lower() != "i agree"):
    #         print("User did not accept! Program exiting")
    #         exit()
    #     print("\nInitializing for Site dump\n")
    #     total_course = len(all_courses)
    #     course_batch = multiprocessing.cpu_count() // 2
    #     if (os.path.isfile(course_completed_path)):
    #         with open(course_completed_path, 'r') as cc:
    #             completed_course = int(cc.readline()) + 1
    #     else:
    #         completed_course = 0
    #     for i in range(completed_course, total_course, course_batch):
    #         if (i + course_batch > total_course):
    #             this_session = (i + course_batch) - total_course
    #         else:
    #             this_session = i + course_batch
    #         cpbar = tqdm(total=course_batch)
    #         print("\nCourses to be downloaded this batch:", i, " to ", this_session)
    #         pool = multiprocessing.Pool(multiprocessing.cpu_count())  # Num of CPUs
    #         with pool as p:
    #             p.map(downloader, (all_courses[j] for j in range(i, this_session) if (
    #                 False if (len(all_courses[j]["access"]["related_passes"]) == 0) else True if (
    #                     course_has_access(all_courses[j])) else False) and 1 or print(
    #                 "Course not in subscription access pack. Skipping ..")))
    #             p.close()
    #             p.join()
    #         update_downloaded(str(i))
    #         print("\nCourse batch successfully completed downloading.. Starting Next batch..")
    #         sleep(1)
    #     os.remove(course_completed_path)
    #     print("Site rip is done!\n")
    # else:
    print(
        "Free Subscription Detected! Do not enter courses not accessible with your account...\n") if siterip == 0 else 0
    custom_path = int(input("\nChoose download location\n1.Current location\n2.Custom location\n3.NA (for multiple learning path download option)\n"))
    if custom_path == 3:
        custom = True
    elif custom_path == 2:
        save_path = input("\nWhere would you like to download your courses? Please put the full path here\n")
        custom = True
    elif custom_path != 1:
        print("Please select download location option 1 or 2!")
        exit()
    choice = int(input(
        "\nChoose Method Of Selecting Course\n1.Enter url\n2.Choose from the above listed course\n3.Download a select number of courses from the above list\n4.Download a bunch of courses from the above list using a range\n5.Download courses of specified learning path\n6.Download multiple learning paths\n"))
    if (choice == 1):
        url = input("Paste the url\n")
        flag = 1
        try:
            for i in all_courses:
                if (i["url"] == url):
                    choice = i
                    flag = 0
            if (flag == 1):
                raise Exception
        except:
            print('Course not found,Recheck url or Choose other method for selecting course\n')
            exit()
        course = choice
        if (course_has_access(course)):
            downloader(course)
        else:
            exit("You do not have the subscription pass access to this course")

    elif (choice == 2):
        choice = int(input("Please enter the number corresponding to the course you would like to download\n"))
        course = all_courses[choice]
        if (course_has_access(course)):
            downloader(course)
        else:
            exit("You do not have the subscription/pass to access to this course")
    elif (choice == 3):
        print("Enter the course numbers to download. Enter \"Done\" to Finish entering courses")
        course_list = []
        while (True):
            choice = input()
            if (choice.lower() == "done"):
                break
            else:
                if (0 <= int(choice) <= len(all_courses)):
                    course_list.append(int(choice))
                else:
                    print("Invalid Choice")
                    continue
        for course_select in course_list:
            course = all_courses[course_select]
            if (course_has_access(course)):
                downloader(course)
            else:
                print("You do not have the subscription/pass to access to this course")
                continue
    elif (choice == 4):
        lowerlimit = int(input("Enter the starting course number(Inclusive)\n"))
        upperlimit = int(input("Enter the closing course number(Inclusive)\n"))
        if (lowerlimit < 0 or lowerlimit > len(all_courses) - 1):
            exit("Invalid lower limit..")
        if (upperlimit < 0 or upperlimit > len(all_courses) - 1):
            exit("Invalid upper limit..")
        for course_select in range(lowerlimit, upperlimit + 1):
            course = all_courses[course_select]
            if (course_has_access(course)):
                downloader(course)
            else:
                print("You do not have the subscription/pass to access to this course")
                continue
    elif (choice == 5):
        learning_path = str(input("\nEnter the learning path title you want to download\n(See https://my.ine.com/learning-paths for paths)\n"))
        path_courses = {}
        with open('ine_courses_index.txt', 'r') as f_raw:
            f_index = f_raw.readlines()
            for course in all_courses:
                try:
                    for path in course['learning_paths']:
                        if path['name'].lower() == learning_path.lower():
                            for line in f_index:
                                if course['name'] in line and (course['name'] + ' ') not in line:
                                    path_courses[line.partition('.')[2][1:].replace('\n','')] = int(line.partition('.')[0])
                                    break
                except:
                    pass
            if len(path_courses) == 0:
                print(f"No courses could be found for {learning_path}, please verify your input!")
                exit()
            else:
                print(f"\n>> {len(path_courses)+1} courses will be downloaded for the '{learning_path}' learning path. <<\n")
        download_learning_path(path_courses, learning_path, all_courses)
    elif (choice == 6):
        print(
            "\nEnter the learning path title and storage location divided by a '|'\nExample: Course123 | C:/somewhere/course123\nType 'done' to finish entering paths.\n(See https://my.ine.com/learning-paths for paths)\n")
        path_list = {}
        while (True):
            path_choice = str(input())
            if (path_choice.lower() == "done"):
                break
            else:
                choices = path_choice.split('|')
                path_list[choices[0].strip()] = choices[1].strip()
        path_courses = {}
        for learning_path in path_list:
            path_nbr = list(path_list.keys()).index(learning_path)
            print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>> Downloading learning path {int(path_nbr) + 1} of {len(path_list)}! <<<<<<<<<<<<<<<<<<<<<<<<<<<')
            save_path = path_list[learning_path]
            with open('ine_courses_index.txt', 'r') as f_raw:
                f_index = f_raw.readlines()
                for course in all_courses:
                    try:
                        for path in course['learning_paths']:
                            if path['name'].lower() == learning_path.lower():
                                for line in f_index:
                                    if course['name'] in line and (course['name'] + ' ') not in line:
                                        path_courses[line.partition('.')[2][1:].replace('\n', '')] = int(
                                            line.partition('.')[0])
                                        break
                    except:
                        pass
            download_learning_path(path_courses, learning_path, all_courses)
    else:
        exit("Invalid choice!\n")
