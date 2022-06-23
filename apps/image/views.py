import io
from PIL import Image as im
import torch

from django.shortcuts import render
from django.views.generic.edit import CreateView

from .models import ImageModel
from .forms import ImageUploadForm

import urllib.request
import json

#  0) 절대경로 path 설정
abs_path = 'C:/Users/crid2/django_yolo_web/'

# 1) 컬러함수 필요 라이브러리
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import numpy as np

# 2) 처음 서버 작동시 로드됨
model = load_model(abs_path + 'yolov5_code/train_file/color.h5')

# 3) 연결코드
def color_classfication(numpy_value) :
        global color_result
        crop_image = im.fromarray(numpy_value , mode=None)
        crop_image.save('media/crop/crop0.jpg')
        img_src = 'media/crop/crop0.jpg'
        test_img = image.load_img(img_src, target_size=(200, 200))
        x = image.img_to_array(test_img)
        x = np.expand_dims(x, axis=0)
        image_ = np.vstack([x])
        classes = model.predict(image_, batch_size=10)
        print('##### cloths image result ####')
        print()
        print('pred - ', classes[0])
        print('color :' , np.argmax(classes[0]))
        print()
        color_result = int(np.argmax(classes[0]))
        if color_result == 0 :
            color_result = 'balck'
        elif color_result == 1 :
            color_result = 'blue'
        elif color_result == 2 :
            color_result = 'green'
        elif color_result == 3 :
            color_result = 'pattern'
        elif color_result == 4 :
            color_result = 'red'
        else :
            color_result = 'white'



class UploadImage(CreateView):
    model = ImageModel
    template_name = 'image/imagemodel_form.html'
    fields = ["image"]

    def post(self, request, *args, **kwargs):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid(): # is_valid() 메서드 데이터의 유효성 검사하는 역활
            img = request.FILES.get('image')
            img_instance = ImageModel(
                image=img
            )
            img_instance.save() # 넘파이나 바이너리로 저장하는 기능
            uploaded_img_qs = ImageModel.objects.filter().last()
            img_bytes = uploaded_img_qs.image.read()
            img = im.open(io.BytesIO(img_bytes))


            path_hubconfig = abs_path + "yolov5_code" # yolov5 폴더 루트
            path_weightfile = abs_path + "yolov5_code/train_file/yolov5s.pt" # yolov5 가중치로 학습한 pt파일위치
            model = torch.hub.load(path_hubconfig, 'custom', path=path_weightfile, source='local')


            # 이미지 라벨 갯수 옵션 ( 보통 2개로 세팅 (상의,하의 ) , 사진이 1인 전신샷이라고 가정)
            model.max_det = 1
            # 라벨 지정 학률 (너무 낮은 확률이면 애매한 옷도 모두 지정해버림)
            model.conf = 0.25

            # ai모델 추론 후 모든 데이터값 results 저장됨
            results = model(img, size=640)

            # 라운딩 박스 세팅수와 crops 이미지 갯수가 불일치 에러
            crops = results.crop(save=False)  # cropped detections dictionary , True 이미지 생성
            # model.max_det = 1 개일때 객체가 0이면 'None'값을 반환
            try :
                cloths_label = crops[0]['label']

                # 4) 크롭된 이미지 색깔판별 함수 호출 color_classfiaction()
                # [:,:,::-1] BGR -> RGB 값으로 전환 넘파이를 이미지 저장시 색상반전을 보정역활
                color_classfication(crops[0]['im'][:, :, ::-1])

                print('black: 0, blue: 1, green: 2, pattern: 3, red: 4, white: 5')
                print(cloths_label)
                print(crops[0]['im'].shape)

            except IndexError :
                print('NO detect , try again ')
                cloths_label = 'No detect'



            results.render()
            for img in results.imgs:
                img_base64 = im.fromarray(img)
                # 결과 저장 및 폴더지정
                img_base64.save("media/yolo_out/result.png" , format="JPEG")
            inference_img = "/media/yolo_out/result.png"

            # 딕셔너리를 json으로 변환

            cloths_data = {'cloths_label' : cloths_label ,
                            'color_code' : color_result}


            # 모델의 라벨과 컬러를 담은 json 파일은 cloths_json으로 저장됨
            cloths_json = json.dumps(cloths_data)




        # 템플릿을 사용하지 않는 경우 필요없음
            form = ImageUploadForm()
            context = {
                "form": form,
                "inference_img": inference_img,
                'cloths_label' : cloths_label,
                'cloths_json' : cloths_json

            }
            return render(request, 'image/imagemodel_form.html', context)

        else:
            form = ImageUploadForm()
        context = {
            "form": form
        }
        return render(request, 'image/imagemodel_form.html', context)




