import cv2

# Load the cascade
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Captures video from laptop webcam
cap = cv2.VideoCapture(0)

# Run this loop a few times so the person being recorded has a chance
# to get their face squarer to the camera before the picture is taken
def start_camera_recog(loops):
    counter = 0
    while counter < loops:
        _, img = cap.read()
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Detect the faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        # Draw the rectangle around each face

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            roi_color = img[y:y + h, x:x + w]

        cv2.imshow('img', img)

        k = cv2.waitKey(33) & 0xff
        counter+=1

def capture_faces():
    captured_face = False
    while True:
        # Read the frame
        _, img = cap.read()
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Detect the faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        # Draw the rectangle around each face

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            roi_color = img[y:y + h, x:x + w]
            cv2.imwrite(str(w) + str(h) + '_faces.jpg', roi_color)
            captured_face = True

        # Display
        cv2.imshow('img', img)
        # Stop if escape key is pressed
        k = cv2.waitKey(33) & 0xff
        if captured_face:
            break


start_camera_recog(60)
capture_faces()
# Release the VideoCapture object
cap.release()

