#!/usr/bin/env python

from availability_builder import ResourceAvailability


def main():
    local = ResourceAvailability()
    local.get_availability()


if __name__ == '__main__':
    main()
