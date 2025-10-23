from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import time
import os

HEIGHT = 600
WIDTH = 800

def opening(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    kernel = np.array([[0,1,0],[1,1,1],[0,1,0]], np.uint8)
    img = cv2.erode(img, kernel, iterations=3)
    img = cv2.dilate(img, kernel, iterations=3)
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
    contours = [c for c in contours if cv2.contourArea(c) > 1000]
    if not contours:
        return img
    out = np.zeros_like(img)
    cv2.drawContours(out, [max(contours, key=cv2.contourArea)], -1, 255, -1)
    return out

def red_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
    mask2 = cv2.inRange(hsv, (170, 100, 100), (180, 255, 255))
    mask = cv2.bitwise_or(mask1, mask2)
    masked = cv2.bitwise_and(img, img, mask=mask)
    return opening(masked)

def split_by_size(img, size):
    rows = int(np.ceil(img.shape[0] / size[0]))
    cols = int(np.ceil(img.shape[1] / size[1]))
    return [chunk for row in np.array_split(img, rows, axis=0)
                  for chunk in np.array_split(row, cols, axis=1)]

def get_target_point(img):
    try:
        coordinates_x = {}
        coordinates_y = {}

        temp = get_coordinates(img)
        coordinates_x["top"] = temp[1][0]
        coordinates_y["top"] = temp[0][0]
        img = cv2.rotate(img,cv2.ROTATE_90_CLOCKWISE)

        temp = list(temp)
        temp.clear()
        temp = get_coordinates(img)
        coordinates_x["left"] = temp[0][0]
        coordinates_y["left"] = abs(HEIGHT - temp[1][0])
        img = cv2.rotate(img,cv2.ROTATE_90_CLOCKWISE)
        img = cv2.rotate(img,cv2.ROTATE_90_CLOCKWISE)

        temp = list(temp)
        temp.clear()
        temp = get_coordinates(img)
        coordinates_x["right"] = abs(WIDTH - temp[0][0])
        coordinates_y["right"] = temp[1][0]
        img = cv2.rotate(img,cv2.ROTATE_90_CLOCKWISE)

        cv2.line(img,(coordinates_x["top"],coordinates_y["top"]),(coordinates_x["right"],coordinates_y["right"]),(100,0,0),thickness=10,lineType=cv2.LINE_8,shift=0)
        cv2.imwrite("../img/result/line_1.jpg",img)
        cv2.line(img,(coordinates_x["right"],coordinates_y["right"]),(coordinates_x["left"],coordinates_y["left"]),(100,0,0),thickness=10,lineType=cv2.LINE_8,shift=0)
        cv2.imwrite("../img/result/line_2.jpg",img)
        cv2.line(img,(coordinates_x["left"],coordinates_y["left"]),(coordinates_x["top"],coordinates_y["top"]),(100,0,0),thickness=10,lineType=cv2.LINE_8,shift=0)

        # if  (abs(coordinates_x["left"] - coordinates_x["right"]))>=WIDTH*0.6:
        #     return "goal"
        return get_center_point(coordinates_x["left"],coordinates_x["right"],coordinates_x["top"])
    except Exception:
        return "ERROR"

def get_center_point(right,left,top):
    result = ((right+left)/2 + top)//2
    if result < WIDTH//3:
        return "left"
    elif result < WIDTH//3*2:
        return "forward"
    else:
        return "right"
        
def get_coordinates(img):
    white_pixels = np.where(img == 255)
    return white_pixels

def merge_chunks(chunks, original_shape, size):
    """分割した画像チャンクを1枚に戻す"""
    h, w, c = original_shape
    row_size, col_size = size
    rows = int(np.ceil(h / row_size))
    cols = int(np.ceil(w / col_size))

    # 行ごとにまとめる
    merged_rows = []
    for r in range(rows):
        start = r * cols
        end = start + cols
        row_imgs = chunks[start:end]
        merged_row = np.concatenate(row_imgs, axis=1)
        merged_rows.append(merged_row)

    # 全体を縦に結合
    merged = np.concatenate(merged_rows, axis=0)
    # サイズを元にトリミング（分割時の端数ズレ対策）
    merged = merged[:h, :w]
    return merged

def imgprocess(img):
    chunk =  (img.shape[0] , img.shape[1] // 4 )
    afImg = split_by_size(img,chunk)
    with ThreadPoolExecutor(max_workers=8) as executor:
        rsImg = list(executor.map(red_mask, afImg))
    merge = merge_chunks(rsImg,img.shape,chunk)
    result = get_target_point(merge)
    if result == "ERROR":
        return "right"
    else:
        return result



def main():
    path = "../img/original/"
    files = os.listdir(path)
    for fname in files:
        try:
            img = cv2.imread(path+fname)
            chunk =  (img.shape[0] , img.shape[1] // 4 )
            afImg = split_by_size(img,chunk)

            st = time.time()
            with ThreadPoolExecutor(max_workers=8) as executor:
                rsImg = list(executor.map(red_mask, afImg))
            print(f"終了: {time.time() - st:.3f}秒")

            os.makedirs("img", exist_ok=True)
            for i, im in enumerate(rsImg):
                cv2.imwrite(f"../img/chatgpt{i}.png", im)

            merge = merge_chunks(rsImg,img.shape,chunk)

            print(get_target_point(merge))

            cv2.imwrite(f"../img/result/result-{fname}.png",merge)
        except Exception:
            pass
if __name__ == "__main__":
    main()