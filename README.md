# danbooru_scraper

scrape from danbooru.

use like below.

    python -u danbooru_scraper.py \
        --danbooru_username (username) \
        --danbooru_apikey (apikey) \
        --search_query 'hatsune_miku rating:g order:score' \
        --need_file_ext 'jpg,jpeg,png,webp' \
        --need_data_num 100 &

see log file "output_log_\*.txt" and result "output_dir_\*".

search query usage https://danbooru.donmai.us/wiki_pages/help:cheatsheet
