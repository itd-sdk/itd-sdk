from time import sleep
from random import choice

from itd import ITDClient

MIN_USERS = 200  # Минимальное количество пользователей для статистики
MAX_PAGES = 100  # Максимум страниц для сбора

c = ITDClient(cookies=input('token: '))

clans = {}
users = set()
seen_posts = set()

def add_user(user):
    """Добавить пользователя в статистику"""
    if user.id in users:
        return
    users.add(user.id)
    avatar = user.avatar or '❓'
    clans[avatar] = clans.get(avatar, 0) + 1

print('1. Сбор популярных пользователей (who to follow)...')
try:
    popular = c.get_who_to_follow()
    for user in popular:
        add_user(user)
    print(f'   Добавлено: {len(popular)}, всего: {len(users)}')
    sleep(3)
except Exception as e:
    print(f'   Ошибка: {e}')

print('\n2. Сбор из ленты...')
page = 0
while page < MAX_PAGES:
    posts, pagination = c.get_posts(cursor=page)
    if not posts:
        print(f'   Посты закончились на странице {page}')
        break
    
    # Проверка на дубликаты постов
    new_posts = [p for p in posts if p.id not in seen_posts]
    if not new_posts:
        print(f'   Дубликаты постов на странице {page}, останавливаемся')
        break
    
    for post in new_posts:
        seen_posts.add(post.id)
        add_user(post.author)
    
    page += 1
    print(f'\r   Страница {page}, уникальных постов: {len(seen_posts)}, пользователей: {len(users)}', end='')
    
    # Если набрали достаточно пользователей и посты начали дублироваться — хватит
    if len(users) >= MIN_USERS and page > 20:
        break
    
    sleep(4)  # Задержка чтобы не забанили

print()

print('\n3. Сбор через подписчиков популярных...')
# Берём первых 10 популярных и собираем их подписчиков
sample_count = 0
for user in popular[:10]:
    if page >= MAX_PAGES:
        break
    
    username = getattr(user, 'username', None)
    if not username:
        continue
    
    try:
        p = 1
        while p <= 3:  # Максимум 3 страницы с каждого
            followers, pagination = c.get_followers(username, limit=30, page=p)
            if not followers:
                break
            for follower in followers:
                add_user(follower)
            p += 1
            sample_count += len(followers)
            print(f'\r   @{username}: страница {p-1}, всего: {len(users)}', end='')
            sleep(2)
            if not pagination.has_more:
                break
        sleep(3)
    except Exception:
        pass

print(f'\n\n========================================')
print(f'Всего пользователей: {len(users)}')
print(f'Всего уникальных постов: {len(seen_posts)}')
print(f'========================================\n')

if not clans:
    print('Нет данных для отображения')
else:
    for i, (clan, count) in enumerate(dict(sorted(clans.items(), key=lambda item: item[1], reverse=True)).items(), 1):
        print(f'{i}: {clan} - {count} ({count / len(users) * 100:.1f}%)')
