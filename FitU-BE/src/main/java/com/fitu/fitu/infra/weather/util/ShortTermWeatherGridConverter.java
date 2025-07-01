package com.fitu.fitu.infra.weather.util;

public class ShortTermWeatherGridConverter {

    private static final double RE = 6371.00877; // 지구 반경 (km)
    private static final double GRID = 5.0; // 격자 간격 (km)
    private static final double SLAT1 = 30.0; // 투영 위도1 (degree)
    private static final double SLAT2 = 60.0; // 투영 위도2 (degree)
    private static final double OLON = 126.0; // 기준 경도 (degree)
    private static final double OLAT = 38.0; // 기준 위도 (degree)
    private static final double XO = 43; // 기준 X좌표 (GRID)
    private static final double YO = 136; // 기준 Y좌표 (GRID)

    public static Grid convert(final double lat, final double lon) {
        final double DEGRAD = Math.PI / 180.0;

        final double re = RE / GRID;
        final double slat1 = SLAT1 * DEGRAD;
        final double slat2 = SLAT2 * DEGRAD;
        final double olon = OLON * DEGRAD;
        final double olat = OLAT * DEGRAD;

        double sn = Math.tan(Math.PI * 0.25 + slat2 * 0.5) / Math.tan(Math.PI * 0.25 + slat1 * 0.5);
        sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);

        double sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5);
        sf = Math.pow(sf, sn) * Math.cos(slat1) / sn;

        double ro = Math.tan(Math.PI * 0.25 + olat * 0.5);
        ro = re * sf / Math.pow(ro, sn);

        double ra = Math.tan(Math.PI * 0.25 + lat * DEGRAD * 0.5);
        ra = re * sf / Math.pow(ra, sn);

        double theta = lon * DEGRAD - olon;
        if (theta > Math.PI) theta -= 2.0 * Math.PI;
        if (theta < -Math.PI) theta += 2.0 * Math.PI;
        theta *= sn;

        final int nx = (int) Math.floor(ra * Math.sin(theta) + XO + 0.5);
        final int ny = (int) Math.floor(ro - ra * Math.cos(theta) + YO + 0.5);

        return new Grid(nx, ny);
    }

    public record Grid(int nx, int ny) {}
}
