## Raspbian packages
```
sudo apt-get install libzbar0
sudo apt-get install python3-pip
```

## Python packages
```
sudo pip3 install opencv-python
sudo pip3 install pyzbar
sudo pip3 install imutils
```

## Run
```
python detect_barcode.py -c
```

### Raspbery pi camera
```
python detect_barcode.py -c --use-pi-camera
```

## Help
```
python detect_barcode.py --help
```
