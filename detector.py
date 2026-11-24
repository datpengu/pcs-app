
from pathlib import Path

from ultralytics import YOLO


class PersonDetector:
    def __init__(self, model_name="yolo11n.pt", confidence=0.25):
        app_dir = Path(__file__).resolve().parent
        model_path = Path(model_name)
        if not model_path.is_absolute():
            model_path = app_dir / model_path
        print("Loading YOLO model...")
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.tracker_config = app_dir / "bytetrack.yaml"
        print("YOLO model loaded!")

    def track(self, frame):
        results = self.model.track(
            frame,
            persist=True,
            tracker=str(self.tracker_config),
            classes=[0],
            conf=self.confidence,
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
