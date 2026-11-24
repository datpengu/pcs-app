
from ultralytics import YOLO


class PersonDetector:
    def __init__(self):
        print("Loading YOLO model...")
        self.model = YOLO("yolo11n.pt")
        print("YOLO model loaded!")

    def track(self, frame):
        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=[0],
            conf=0.25,
            verbose=False
        )

        people = []

        for result in results:
            if result.boxes is None:
                continue

            if result.boxes.id is None:
                continue

            boxes = result.boxes.xyxy.cpu().numpy()
            ids = result.boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)

                people.append({
                    "id": track_id,
                    "box": (x1, y1, x2, y2)
                })

        return people
