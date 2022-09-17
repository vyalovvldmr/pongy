# Pongy

Ping-pong multiplayer client-server game up to 4 players over network in early development stage.

## Requires

Python 3.10

## Install

```
$ pip install pongy
```

or

```
$ poetry shell
$ poetry add pongy
```

## Run Server

```
$ pongy -d -h 0.0.0.0 -p 8888
```

## Run Client

```
$ pongy -h 192.168.1.1 -p 8888
```

![UI screenshot](https://github.com/vyalovvldmr/pongy/blob/master/screen.png?raw=true)

## TODO

- [ ] Racket bouncing
- [ ] Score counting
- [ ] Test coverage
- [ ] Think about UDP vs websockets (it should be better for realtime)
- [ ] Think about p2p vs client-server