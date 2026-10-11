# Sega FILM/Cinepak 정적 형식 검증기

`validate_cpk.py`는 표준 Python 3 라이브러리만 사용하며, **원본에서 4바이트 패킷/스트립/청크 정렬, 2바이트 Sega 확장, physical−declared size bias 8을 확인한** Sega FILM/Cinepak 변형에만 사용한다. 원본에서 다른 패턴이 나오면 이 검증기를 끼워 맞추지 말고 프로필을 분기한다.

## 실행

```bash
python3 adapters/sega-film-cpk/validate_cpk.py --self-test
python3 adapters/sega-film-cpk/validate_cpk.py build.CPK --original original.CPK
```

검사 범위: FILM/FDSC/STAB 구조, 시간값, 패킷/청크/스트립 정렬 및 선언 크기, 키프레임 플래그 일치, 원본 PCM 정확 일치, 스트립 geometry, 매체 내 고정 CPK 크기. 검증 불일치 시 종료 코드 1로 빌드를 실패 처리한다. `--original` 없이 실행하면 원본 PCM/PTS 및 고정 범위까지 검증할 수 없으므로 그 상태는 완전한 빌드 게이트가 **아니다**.

이 코드는 인코더나 리패커가 아니며 코드북 내부 의미·영상 품질·섹터 EDC/ECC·디스크 재추출·xdelta 역적용·실제 에뮬레이터/하드웨어 재생을 확인하지 않는다. 별도 검증과 사용자의 게임 재생 결과를 요구한다.

참고: [채택 프로필](../../config/sega-saturn-film-cinepak.md), [실패 사례](../../research/sega-saturn-cpk-alignment-case.md).
