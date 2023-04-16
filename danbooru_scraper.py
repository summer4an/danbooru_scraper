import os, sys, argparse, subprocess, datetime, textwrap
import json
from pybooru import Danbooru

usage = textwrap.dedent('''
    scrape from danbooru.
    use like below.
        python -u danbooru_scraper.py \\
            --danbooru_username (username) \\
            --danbooru_apikey (apikey) \\
            --search_query 'hatsune_miku rating:g order:score' \\
            --need_file_ext 'jpg,jpeg,png,webp' \\
            --need_data_num 100 &
    see log file "output_log_*.txt" and result "output_dir_*".

    search query usage https://danbooru.donmai.us/wiki_pages/help:cheatsheet
''')

class MyPrint:
    '''
        print out to both terminal and logfile with datetime header.
    '''
    def __init__(self, output_log_filename):
        self.console = sys.stdout
        self.logfile = open(output_log_filename, 'a')
        self.start_with_header = True
    def write(self, message):
        header = datetime.datetime.now().strftime('[%Y%m%d_%H%M%S] ')
        if self.start_with_header == True:
            message = header + message
        if message[-1]=='\n':
            message = message[:-1]
            self.start_with_header = True
        else:
            self.start_with_header = False
        message = message.replace('\n', '\n'+header)
        if self.start_with_header == True:
            message += '\n'
        try:
            if self.console is not None: self.console.write(message)
        except:
            self.console = None
        try:
            if self.logfile is not None: self.logfile.write(message)
        except:
            self.logfile = None
    def flush(self):
        try:
            if self.console is not None: self.console.flush()
        except:
            self.console = None
        try:
            if self.logfile is not None: self.logfile.flush()
        except:
            self.logfile = None

def DanbooruScrape():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=usage)

    parser.add_argument('--danbooru_username', type=str, required=True)
    parser.add_argument('--danbooru_apikey', type=str, required=True)
    parser.add_argument('--search_query', type=str, required=True, help="ex. hatsune_miku rating:g order:score")
    parser.add_argument('--need_data_num', type=int, required=False, default=100)
    parser.add_argument('--need_file_ext', type=str, required=False, default='jpg,jpeg,png,webp', help='ex. jpg,jpeg,png,webp  ex. *')
    now_datetime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    parser.add_argument('--output_dir', type=str, required=False, default=f'output_dir_{now_datetime}')
    parser.add_argument('--output_log_filename', type=str, required=False, default=f'output_log_{now_datetime}.txt')

    args = parser.parse_args()

    sys.stdout = sys.stderr = MyPrint(args.output_log_filename)

    print(f'command line:{sys.argv}')
    print(f'original args:{args}')

    args.output_dir = args.output_dir.rstrip('/')
    args.output_dir_json_original = os.path.join(args.output_dir,'json_original')
    args.need_file_ext = args.need_file_ext.split(',')
    if '*' in args.need_file_ext:
        print('included "*" in need_file_ext. download all ext.')
        args.need_file_ext = ['*',]

    print(f'modified args:{args}')

    print(f'output_dir:{args.output_dir}')
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.output_dir_json_original, exist_ok=True)

    danbooru = Danbooru('danbooru', username=args.danbooru_username, api_key=args.danbooru_apikey)

    done_num=0
    for iteration in range((args.need_data_num-1)//100+1):
        get_num = min(100,args.need_data_num-done_num)
        print(f'done_num:{done_num} get_num:{get_num} progress:{done_num/args.need_data_num*100:4.2f}%')
        try:
            data_list = danbooru.post_list(tags=args.search_query, limit=get_num, random=False, page=iteration+1)
        except Exception as e:
            print(f'error. can not get list. iteration:{iteration}')
            exit(-1)
        if data_list==[]:
            print(f'error. empty data_list.')
            exit(-1)
        print(f'data_list len:{len(data_list)}')

        for target_data in data_list:
            done_num+=1

            if not 'file_url' in target_data:
                print('no file_url. skip.')
                continue

            file_url = target_data['file_url']
            print(f'done_num:{done_num} file_url:{file_url}')

            temp = f'{done_num:08d}_'+file_url.split('/')[-1]
            output_filename_base,output_path_ext = os.path.splitext(temp)
            output_path_ext = output_path_ext.lstrip('.')
            output_path_image = os.path.join(args.output_dir, output_filename_base+'.'+output_path_ext)
            output_path_txt = os.path.join(args.output_dir, output_filename_base+'.txt')
            output_path_json_original = os.path.join(args.output_dir_json_original, output_filename_base+'.txt')
            if args.need_file_ext[0]!='*' and not output_path_ext.lower() in args.need_file_ext:
                print(f'not need ext. skip. {output_path_ext} {output_path_image}')
                continue
            if os.path.isfile(output_path_image) and os.path.isfile(output_path_txt) and os.path.isfile(output_path_json_original):
                print(f'already downloaded. skip. {output_path_image}')
                continue

            with open(output_path_json_original, 'w') as fp:
                json.dump(target_data,fp,indent=4)

            with open(output_path_txt, 'w') as fp:
                text = target_data['tag_string_character'] + ' ' + target_data['tag_string_general']
                text = text.replace(' ', ', ')
                print(text, file=fp)

            ret = subprocess.run(["wget", file_url, '-o', '/dev/null', '-O', output_path_image], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            # print(ret.returncode)
            # print(ret.stdout.decode("utf-8"))
            # print(ret.stderr.decode("utf-8"))
            if ret.returncode!=0:
                print(f'error. wget return {ret.returncode}')
                exit(-1)

        if len(data_list)!=get_num:
            print(f'no more data. len(data_list):{len(data_list)} get_num:{get_num}')
            break

    print(f'all done. done_num:{done_num}')

if __name__ == "__main__":
    DanbooruScrape()
