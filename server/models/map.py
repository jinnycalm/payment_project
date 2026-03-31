from typing import TypedDict, Literal, NotRequired

class MapInfo(TypedDict):
    '''카카오 API로 받아온 결과'''

    id: str                                 # 매장 고유 ID
    place_name: str                         # 매장 이름
    category_group_code: Literal['FD6', 'CE7', 'CS2', 'HP8','PM9', 'MT1', 'AC5', 'PK6', 'OL7', 'SW8', 'CT1', 'EX1']     # 카테고리 코드
    category_group_name: str                # 카테고리명
    phone: NotRequired[str]                 # 전화번호
    address_name: NotRequired[str]          # 지번 주소
    road_address_name: NotRequired[str]     # 도로명 주소
    x: str                                  # x 좌표
    y: str                                  # y 좌표
    place_url: NotRequired[str]             # 장소 상세페이지 URL