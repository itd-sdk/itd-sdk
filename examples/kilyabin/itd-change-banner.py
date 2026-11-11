#!/usr/bin/env python3
# Full quality needs the banner extra: uv add itd-sdk[banner]; without it a simple low quality mode is used
import sys
from argparse import ArgumentParser
from os import getenv
from os.path import isfile

from itd import Me, init_client
from itd.core.auth import AccessAuth


def main():
    parser = ArgumentParser(description='Draw an image as banner strokes and set it as profile banner')

    parser.add_argument('--token', default=getenv('ITD_TOKEN'), help='Access token (or ITD_TOKEN env var)')

    parser.add_argument('--file', required=True, help='Path to image file')

    parser.add_argument('--engine', default='layers', choices=['layers', 'strokes', 'exact'], help='layers - graphics, strokes - photos')

    args = parser.parse_args()

    if not args.token:
        print('❌ Токен не задан (--token или ITD_TOKEN)', file=sys.stderr)
        quit()

    file_path = args.file

    if not isfile(file_path):
        print(f'❌ Файл не найден: {file_path}', file=sys.stderr)
        quit()

    try:
        client = init_client('banner', auth=AccessAuth(args.token))
        drawing = Me(client).update_banner(file_path, engine=args.engine, on_progress=lambda stage, done: print(f'\r⏳ {stage}: {done:.0%}   ', end=''))
        print()

        print('✅ Баннер обновлён!')
        print('📄 Информация о рисунке:')
        print(f'  id: {drawing.id}')
        print(f'  url: {drawing.url}')
        print(f'  штрихов: {len(drawing.ops)}')
        print(f'  ΔE: {drawing.dE:.2f}')

    except Exception as e:
        print('❌ Произошла ошибка:', e, file=sys.stderr)
        quit()


if __name__ == '__main__':
    main()
