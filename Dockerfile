# 베이스 이미지 설정
FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

# 패키지 목록 업데이트 및 Git 설치
RUN apt-get update && apt-get install -y git

# Git 환경 변수 설정
ENV GIT_PYTHON_GIT_EXECUTABLE=/usr/bin/git

# 프로젝트의 requirements.txt 파일을 컨테이너로 복사하고 패키지를 설치
COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt

# 기본 작업 디렉토리 설정
WORKDIR /workspace

# 기본 쉘을 /bin/bash로 설정
CMD ["/bin/bash"]
