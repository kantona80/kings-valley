#!/usr/bin/env python3

import argparse
import struct
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


class ArgumentParser(object):

    def __init__(self):
        self._args = None
        self._parser = argparse.ArgumentParser(prog='tiled2kv', description='Scans the directory for tmx files and \
                                                                             converts them to KingsValley Amiga format')
        self._parser.add_argument('-i', '--input', default='.', help='Folder containing the maps to scan.')

    def parse(self):
        self._args = self._parser.parse_args()
        return self._args

    @property
    def input(self):
        return self._args.input


class TmxScanner(object):
    _known_patterns = ["*.tmx"]

    def __init__(self, input_folder):
        self._paths = []
        self._input_folder = input_folder

    def scan(self):
        for pattern in TmxScanner._known_patterns:
            for path in Path(self._input_folder).glob(pattern):
                self._paths.append(path)
        self._paths.sort()
        return self._paths


class TmxParser(object):

    def __init__(self, paths):
        self._paths = paths

    def parse(self):
        assert (len(self._paths) > 0), 'No TMX files have been found in the specified folder'
        for path in self._paths:
            print('Parsing {}...'.format(path))
            tree = ET.parse(path)
            root = tree.getroot()
            size = self._read_map_size(root)
            assert (size[0] in [32, 64]), 'Width must be 32 or 64'
            assert (size[1] == 22), 'Height must be 22'
            background = self._read_layer(root, size, 'fondo')
            foreground = self._read_layer(root, size, 'primer_plano')
            dynamic = self._read_layer(root, size, 'dinamico')
            objects = self._read_objects(root)
            AssertUtil(objects).assert_objects()
            KingValleyMapWriter(path, size, background, foreground, dynamic, objects).write()

    def _read_map_size(self, root):
        return int(root.attrib['width']), int(root.attrib['height'])

    def _read_layer(self, root, size, name):
        print('Reading layer {}'.format(name))
        data = ''
        computed_size = size[0] * size[1]
        for layer in root.iterfind('layer[@name="' + name + '"]'):
            element = layer.findall('data')[0]
            data = (element.text.replace('\n', ''))
        output = [int(d) for d in data.split(',')]
        assert (len(output) == computed_size), 'Layer {} must have a size of {} bytes'.format(name, computed_size)
        assert (len([o for o in output if o <= 255]) == len(output)), 'Tile index greater than 255 detected'
        return output

    def _read_objects(self, root):
        knives = []
        pickaxes = []
        jewels = []
        doors = []
        rdoors = []
        stairs = []
        mummies = []
        walls = []
        for objects in root.iterfind('objectgroup[@name="objetos"]'):
            knives = [knife for knife in objects.iterfind('object[@name="daga"]')]
            pickaxes = [pickaxe for pickaxe in objects.iterfind('object[@name="pico"]')]
            jewels = [jewel for jewel in objects.iterfind('object[@name="joya"]')]
            doors = [door for door in objects.iterfind('object[@name="puerta"]')]
            rdoors = [rdoor for rdoor in objects.iterfind('object[@name="giratoria"]')]
            stairs = [stair for stair in objects.iterfind('object[@name="escalera"]')]
            mummies = [mummy for mummy in objects.iterfind('object[@name="momia"]')]
            walls = [wall for wall in objects.iterfind('object[@name="muro"]')]
        return knives, pickaxes, jewels, doors, rdoors, stairs, mummies, walls


class AssertUtil(object):

    def __init__(self, objects):
        self._objects = objects

    def assert_objects(self):
        print('Reading objects layer')
        assert (len(self._objects) == 8), 'Objects length must be 8'
        self._assert_object(0, 'knives')
        self._assert_object(1, 'pickaxes')
        self._assert_object(2, 'jewels')
        self._assert_doors(3, 'doors', ['entrada', 'salida', 'entrada-salida'])
        self._assert_revolving_doors(4, 'revolving doors', ['derecha', 'izquierda'])
        self._assert_stairs(5, 'stairs', ['sube-derecha', 'baja-izquierda', 'sube-izquierda', 'baja-derecha'])
        self._assert_object_and_type(6, 'mummies', ['blanca', 'azul', 'amarilla', 'naranja', 'roja'])
        self._assert_walls(7, 'walls')

    def _assert_object(self, index, name):
        if len(self._objects[index]) == 0:
            print("\tWarning: {} not found in the object layer".format(name))
        else:
            print('\t{} {} found'.format(len(self._objects[index]), name))

    def _assert_object_and_type(self, index, name, types):
        self._assert_object(index, name)
        for obj in self._objects[index]:
            obj_type = obj.attrib['type']
            assert (obj_type in types) \
                , '{} type must be any of the following {}. {} found.'.format(name, types, obj_type)

    def _assert_doors(self, index, name, types):
        self._assert_object_and_type(index, name, types)
        counter = Counter([obj.attrib['type'] for obj in self._objects[index]])
        in_out = counter['entrada-salida']
        in_door = counter['entrada']
        out_door = counter['salida']
        if in_out > 0:
            assert (in_out > 0 and in_door == 0 and out_door == 0) \
                , "There must be a single door if 'entrada-salida' type is set"
        else:
            assert (in_out == 0 and in_door == out_door and in_door == 1) \
                , "There must be 2 doors if 'entrada-salida' type is not set, one of them should be 'entrada' type " \
                  "and the other one should be 'salida'"

    def _assert_revolving_doors(self, index, name, types):
        self._assert_object_and_type(index, name, types)
        for obj in self._objects[index]:
            properties = obj.iterfind('./properties/property[@name="altura"]')
            heights = [int(property.attrib['value']) for property in properties]
            assert (len(heights) > 0), 'Revolving doors must include a custom property called "altura"'

    def _assert_stairs(self, index, name, types):
        self._assert_object_and_type(index, name, types)
        counter = Counter([stair.attrib['type'] for stair in self._objects[index]])
        up_left = counter['sube-izquierda']
        down_right = counter['baja-derecha']
        up_right = counter['sube-derecha']
        down_left = counter['baja-izquierda']
        assert (up_left == down_right) \
            , 'There must be the same amount of sube-izquierda elements than baja-derecha. Found {} {}' \
            .format(up_left, down_right)
        assert (up_right == down_left) \
            , 'There must be the same amount of sube-derecha elements than baja-izquierda. Found {} {}' \
            .format(up_right, down_left)
        assert ((up_left > 0 and down_right > 0) or (up_right > 0 and down_left > 0)) \
            , 'There must be at least one stair in the map'

    def _assert_walls(self, index, name):
        self._assert_object(index, name)
        for obj in self._objects[index]:
            properties = obj.iterfind('./properties/property[@name="activacion"]')
            activations = [int(property.attrib['value']) for property in properties]
            assert (len(activations) > 0), 'Walls must include a custom property called "activacion"'


class KingValleyMapWriter(object):

    def __init__(self, path, size, background, foreground, dynamic, objects):
        self._path = path
        self._size = size
        self._background = background
        self._foreground = foreground
        self._dynamic = dynamic
        self._objects = objects

    def write(self):
        filename = self._path.name + '.kv'
        print('Writing {}...'.format(filename))
        with open(filename, 'wb') as f:

            f.write(struct.pack('=bb', self._size[0], self._size[1]))  # Map size
            for tile in self._background:  # Background
                f.write(struct.pack('=B', tile))
            for tile in self._foreground:  # Foreground
                f.write(struct.pack('=B', tile))
            f.write(struct.pack('=B', sum([len(item) for item in self._objects])))  # Items count

            self._write_objects_with_dynamic_id(f, 0, 'D')  # Knives
            self._write_objects_with_dynamic_id(f, 1, 'P')  # Pickaxes
            self._write_objects_with_dynamic_id(f, 2, 'J')  # Jewels

            self._write_objects_with_type(f, 3, 'T', ['entrada', 'salida', 'entrada-salida'])  # Doors
            self._write_objects_with_type(f, 4, 'G', ['derecha', 'izquierda'])  # Revolving doors
            self._write_objects_with_type(f, 5, 'E', ['sube-derecha', 'baja-izquierda', 'sube-izquierda',
                                                      'baja-derecha'])  # Stairs
            self._write_objects_with_type(f, 6, 'M', ['blanca', 'azul', 'amarilla', 'naranja', 'roja'])  # Mummies
            self._write_walls(f, 7, 'U')    # Walls

    def _write_objects_with_dynamic_id(self, f, index, object_id):
        for obj in self._objects[index]:
            x = int(obj.attrib['x']) // 10
            y = int(obj.attrib['y']) // 10
            f.write(struct.pack('=BBBB', ord(object_id), x, y, self._get_dynamic_id(x, y)))

    def _get_dynamic_id(self, x, y):
        offset = y * self._size[0] + x
        return self._dynamic[offset]

    def _write_objects_with_type(self, f, index, object_id, type_list):
        for obj in self._objects[index]:
            x = int(obj.attrib['x']) // 10
            y = int(obj.attrib['y']) // 10
            object_type = obj.attrib['type']
            if object_id == 'G':  # Revolving doors.
                properties = obj.iterfind('./properties/property[@name="altura"]')
                heights = [int(property.attrib['value']) for property in properties]
                h = heights[0] if len(heights) > 0 else -1
                f.write(struct.pack('=BBBBB', ord(object_id), x, y, h, type_list.index(object_type)))
            else:
                f.write(struct.pack('=BBBB', ord(object_id), x, y, type_list.index(object_type)))
    
    def _write_walls(self, f, index, object_id):
        for obj in self._objects[index]:
            x = int(obj.attrib['x']) // 10
            y = int(obj.attrib['y']) // 10
            h = int(obj.attrib['height']) // 10
            properties = obj.iterfind('./properties/property[@name="activacion"]')
            activations = [int(property.attrib['value']) for property in properties]
            activation = activations[0] if len(activations) > 0 else -1
            f.write(struct.pack('=BBBBB', ord(object_id), x, y, y + h -1, activation))


def main():
    args = ArgumentParser().parse()
    paths = TmxScanner(args.input).scan()
    TmxParser(paths).parse()


if __name__ == '__main__':
    main()
