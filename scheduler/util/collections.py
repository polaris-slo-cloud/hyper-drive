from typing import TypeVar

def copy_dict[K, V](src: dict[K, V], dest: dict[K, V]):
    '''
    Copies all items from src to dest.
    '''
    for key, value in src.items():
        dest[key] = value
