
import cv2

from detector import PersonDetector
from counter import PeopleCounter


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Could not open camera.")
        return

    detector = PersonDetector()
    counter = PeopleCounter()

    print("pcs-app started! Press Q to quit.")

    while True:
        success, frame = camera.read()

        if not success:
            break

        people = detector.track(frame)

        stats = counter.update(
            people,
            frame.shape[1]
        )

        # Draw virtual entrance line
        line_x = stats["line_x"]

        cv2.line(
            frame,
            (line_x, 0),
            (line_x, frame.shape[0]),
            (255, 0, 0),
            2
        )

        # Draw detected people
        for person in people:
            x1, y1, x2, y2 = person["box"]
            track_id = person["id"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"ID: {track_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # Display statistics
        cv2.putText(
            frame,
            f"Inside: {stats['inside']}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Entered: {stats['entered']}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Exited: {stats['exited']}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

        cv2.imshow("pcs-app | People Counter", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
