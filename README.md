# kulo [![Build Status][build-status-img]][build-status-link] [![PyPI][pypi-version-img]][pypi-version-link]

A tool for managing Mitsubishi Heat Pump systems (mostly?) locally instead of through Kumo Cloud.

This was written primarily because Kumo Cloud never works.

Kulo requires Python 3.8 or newer.

[build-status-img]: https://api.cirrus-ci.com/github/duckinator/kulo.svg
[build-status-link]: https://cirrus-ci.com/github/duckinator/kulo

[pypi-version-img]: https://img.shields.io/pypi/v/kulo
[pypi-version-link]: https://pypi.org/project/kulo

<!--

## Installation

```
$ pip3 install kulo
```

Or download [the latest zipapp
releases](https://github.com/duckinator/kulo/releases/latest/download/kulo.pyz)

-->

## Usage

(Planned; not implemented.)

```
$ kulo login
Kumo Cloud username: <type your username and press enter>
Password: <type your password and press enter>

Found 2 indoor units:
- Main Bedroom
- Main House
$ kulo test
Testing connections to 2 indoor units:

- Main Bedroom: Success
- Main House: Success
$ kulo
Main Bedroom
    Mode:        Heat
    Temperature: 68°F
    Humidity:    48%
    Fan Speed:   3/5

Main House
    Mode:        Heat
    Temperature: 70°F
    Humidity:    49%
    Fan Speed:   2/3
$
```

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/duckinator/kulo.

The code for Kulo is available under the [MIT License](http://opensource.org/licenses/MIT).
